#!/usr/bin/env python
#
# PyODConverter (Python OpenDocument Converter) v1.0.0 - 2008-05-05
#
# This script converts a document from one office format to another by
# connecting to an OpenOffice.org instance via Python-UNO bridge.
#
# Copyright (C) 2008 Mirko Nasato <mirko@artofsolving.com>
#                    Matthew Holloway <matthew@holloway.co.nz>
#                    Alistek Ltd. (www.alistek.com) 
# Licensed under the GNU LGPL v2.1 - http://www.gnu.org/licenses/lgpl-2.1.html
# - or any later version.
#

DEFAULT_OPENOFFICE_PORT = 8100

################## For CSV documents #######################
# Field Separator (1), 	Text Delimiter (2), 	Character Set (3), 	Number of First Line (4)
CSVFilterOptions = "59,34,76,1"
# ASCII code of field separator
# ASCII code of text delimiter
# character set, use 0 for "system character set", 76 seems to be UTF-8
# number of first line (1-based)
# Cell format codes for the different columns (optional)
############################################################

from os.path import abspath
from os.path import isfile
from os.path import splitext
import sys
import time
import subprocess
import logging
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

import uno
import unohelper
from com.sun.star.beans import PropertyValue
from com.sun.star.uno import Exception as UnoException
from com.sun.star.connection import NoConnectException, ConnectionSetupException
from com.sun.star.beans import UnknownPropertyException
from com.sun.star.lang import IllegalArgumentException
from com.sun.star.io import XOutputStream
from com.sun.star.io import IOException
from tools.translate import _

logger = logging.getLogger(__name__)

class DocumentConversionException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class OutputStreamWrapper(unohelper.Base, XOutputStream):
    """ Minimal Implementation of XOutputStream """
    def __init__(self, debug=True):
        self.debug = debug
        self.data = StringIO()
        self.position = 0
        if self.debug:
            sys.stderr.write("__init__ OutputStreamWrapper.\n")

    def writeBytes(self, bytes):
        if self.debug:
            sys.stderr.write("writeBytes %i bytes.\n" % len(bytes.value))
        self.data.write(bytes.value)
        self.position += len(bytes.value)

    def close(self):
        if self.debug:
            sys.stderr.write("Closing output. %i bytes written.\n" % self.position)
        self.data.close()

    def flush(self):
        if self.debug:
            sys.stderr.write("Flushing output.\n")
        pass
    def closeOutput(self):
        if self.debug:
            sys.stderr.write("Closing output.\n")
        pass

class DocumentConverter:
   
    def __init__(self, host='localhost', port=DEFAULT_OPENOFFICE_PORT, ooo_restart_cmd=None):
        self._host = host
        self._port = port
        self._ooo_restart_cmd = ooo_restart_cmd
        self.localContext = uno.getComponentContext()
        self.serviceManager = self.localContext.ServiceManager
        self._resolver = self.serviceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", self.localContext)
        try:
            self._context = self._resolver.resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host, port))
        except IllegalArgumentException, exception:
            raise DocumentConversionException("The url is invalid (%s)" % exception)
        except NoConnectException, exception:
            if self._restart_ooo():
                # We try again once
                try:
                    self._context = self._resolver.resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (host, port))
                except NoConnectException, exception:
                    raise DocumentConversionException("Failed to connect to OpenOffice.org on host %s, port %s. %s" % (host, port, exception))
            else:
                raise DocumentConversionException("Failed to connect to OpenOffice.org on host %s, port %s. %s" % (host, port, exception))

        except ConnectionSetupException, exception:
            raise DocumentConversionException("Not possible to accept on a local resource (%s)" % exception)

    def putDocument(self, data):
        try:
            desktop = self._context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self._context)
        except UnknownPropertyException:
            self._context = self._resolver.resolve("uno:socket,host=%s,port=%s;urp;StarOffice.ComponentContext" % (self._host, self._port))
            desktop = self._context.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", self._context)
        inputStream = self.serviceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self.localContext)
        inputStream.initialize((uno.ByteSequence(data),))
        self.document = desktop.loadComponentFromURL('private:stream', "_blank", 0, self._toProperties(InputStream = inputStream))
        inputStream.closeInput()

    def closeDocument(self):
        self.document.close(True)

    def saveByStream(self, filter_name=None):
        try:
            self.document.refresh()
        except AttributeError, e: # ods document does not support refresh
            pass
        outputStream = OutputStreamWrapper(False)
        try:
            self.document.storeToURL('private:stream', self._toProperties(OutputStream = outputStream, FilterName = filter_name, FilterOptions=CSVFilterOptions))
        except IOException, e:
            print ("IOException during conversion: %s - %s" % (e.ErrCode, e.Message))
            outputStream.close()

        openDocumentBytes = outputStream.data.getvalue()
        outputStream.close()
        return openDocumentBytes
        

    def insertSubreports(self, oo_subreports):
        """
        Inserts the given file into the current document.
        The file contents will replace the placeholder text.
        """
        import os

        for subreport in oo_subreports:
            fd = file(subreport, 'rb')
            placeholder_text = "<insert_doc('%s')>" % subreport
            subdata = fd.read()
            subStream = self.serviceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self.localContext)
            subStream.initialize((uno.ByteSequence(subdata),))

            search = self.document.createSearchDescriptor()
            search.SearchString = placeholder_text
            found = self.document.findFirst( search )
            #while found:
            try:
                found.insertDocumentFromURL('private:stream', self._toProperties(InputStream = subStream, FilterName = "writer8"))
            except Exception, ex:
                print (_("Error inserting file %s on the OpenOffice document: %s") % (subreport, ex))
            #found = self.document.findNext(found, search)

            os.unlink(subreport)

    def joinDocuments(self, docs):
        while(docs):
            subStream = self.serviceManager.createInstanceWithContext("com.sun.star.io.SequenceInputStream", self.localContext)
            subStream.initialize((uno.ByteSequence(docs.pop()),))
            try:
                self.document.Text.getEnd().insertDocumentFromURL('private:stream', self._toProperties(InputStream = subStream, FilterName = "writer8"))
            except Exception, ex:
                print (_("Error inserting file %s on the OpenOffice document: %s") % (docs, ex))

    def convertByPath(self, inputFile, outputFile):
        inputUrl = self._toFileUrl(inputFile)
        outputUrl = self._toFileUrl(outputFile)
        document = self.desktop.loadComponentFromURL(inputUrl, "_blank", 8, self._toProperties(Hidden=True))
        try:
            document.refresh()
        except AttributeError:
            pass
        try:
            document.storeToURL(outputUrl, self._toProperties(FilterName="writer_pdf_Export"))
        finally:
            document.close(True)

    def _toFileUrl(self, path):
        return uno.systemPathToFileUrl(abspath(path))

    def _toProperties(self, **args):
        props = []
        for key in args:
            prop = PropertyValue()
            prop.Name = key
            prop.Value = args[key]
            props.append(prop)
        return tuple(props)

    def _restart_ooo(self):
        if not self._ooo_restart_cmd:
            logger.warning('No LibreOffice/OpenOffice restart script configured')
            return False
        logger.info('Restarting LibreOffice/OpenOffice background process')
        try:
            logger.info('Executing restart script "%s"' % self._ooo_restart_cmd)
            retcode = subprocess.call(self._ooo_restart_cmd, shell=True)
            if retcode == 0:
                logger.warning('Restart successfull')
                time.sleep(4) # Let some time for LibO/OOO to be fully started
            else:
                logger.error('Restart script failed with return code %d' % retcode)
        except OSError, e:
            logger.error('Failed to execute the restart script. OS error: %s' % e)
        return True

