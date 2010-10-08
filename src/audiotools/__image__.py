#!/usr/bin/python

#Audio Tools, a module and set of tools for manipulating audio data
#Copyright (C) 2007-2010  Brian Langenberger

#This program is free software; you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation; either version 2 of the License, or
#(at your option) any later version.

#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.

#You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

from audiotools import construct
import imghdr
import cStringIO
import gettext

gettext.install("audiotools",unicode=True)

def __jpeg__(h, f):
    if (h[0:3] == "FFD8FF".decode('hex')):
        return 'jpeg'
    else:
        return None

imghdr.tests.append(__jpeg__)


#takes a string of file data
#returns an ImageMetrics class if the file can be identified
#raises InvalidImage if there is an error or the file is unknown
def image_metrics(file_data):
    header = imghdr.what(None,file_data)

    file = cStringIO.StringIO(file_data)
    try:
        if (header == 'jpeg'):
            return __JPEG__.parse(file)
        elif (header == 'png'):
            return __PNG__.parse(file)
        elif (header == 'gif'):
            return __GIF__.parse(file)
        elif (header == 'bmp'):
            return __BMP__.parse(file)
        elif (header == 'tiff'):
            return __TIFF__.parse(file)
        else:
            raise InvalidImage(_(u'Unknown image type'))
    finally:
        file.close()

#######################
#JPEG
#######################

class ImageMetrics:
    def __init__(self, width, height, bits_per_pixel, color_count, mime_type):
        self.width = width
        self.height = height
        self.bits_per_pixel = bits_per_pixel
        self.color_count = color_count
        self.mime_type = mime_type

    def __repr__(self):
        return "ImageMetrics(%s,%s,%s,%s,%s)" % \
               (repr(self.width),
                repr(self.height),
                repr(self.bits_per_pixel),
                repr(self.color_count),
                repr(self.mime_type))

class InvalidImage(Exception):
    def __init__(self,err):
        self.err = unicode(err)

    def __unicode__(self):
        return self.err

class InvalidJPEG(InvalidImage): pass

class __JPEG__(ImageMetrics):
    SEGMENT_HEADER = construct.Struct('segment_header',
                                construct.Const(construct.Byte('header'),0xFF),
                                construct.Byte('type'),
                                construct.If(
        lambda ctx: ctx['type'] not in (0xD8,0xD9),
        construct.UBInt16('length')))

    APP0 = construct.Struct('JFIF_segment_marker',
                      construct.String('identifier',5),
                      construct.Byte('major_version'),
                      construct.Byte('minor_version'),
                      construct.Byte('density_units'),
                      construct.UBInt16('x_density'),
                      construct.UBInt16('y_density'),
                      construct.Byte('thumbnail_width'),
                      construct.Byte('thumbnail_height'))

    SOF = construct.Struct('start_of_frame',
                     construct.Byte('data_precision'),
                     construct.UBInt16('image_height'),
                     construct.UBInt16('image_width'),
                     construct.Byte('components'))

    def __init__(self, width, height, bits_per_pixel):
        ImageMetrics.__init__(self, width, height, bits_per_pixel,
                              0, u'image/jpeg')

    @classmethod
    def parse(cls, file):
        try:
            header = cls.SEGMENT_HEADER.parse_stream(file)
            if (header.type != 0xD8):
                raise InvalidJPEG(_(u'Invalid JPEG header'))

            segment = cls.SEGMENT_HEADER.parse_stream(file)
            while (segment.type != 0xD9):
                if (segment.type == 0xDA):
                    break

                if (segment.type in (0xC0,0xC1,0xC2,0xC3,
                                     0xC5,0XC5,0xC6,0xC7,
                                     0xC9,0xCA,0xCB,0xCD,
                                     0xCE,0xCF)): #start of frame
                    segment_data = cStringIO.StringIO(
                        file.read(segment.length - 2))
                    frame0 = cls.SOF.parse_stream(segment_data)
                    segment_data.close()

                    return __JPEG__(width = frame0.image_width,
                                    height = frame0.image_height,
                                    bits_per_pixel = (frame0.data_precision * \
                                                      frame0.components))
                else:
                    file.seek(segment.length - 2,1)

                segment = cls.SEGMENT_HEADER.parse_stream(file)


            raise InvalidJPEG(_(u'Start of frame not found'))
        except construct.ConstError:
            raise InvalidJPEG(_(u"Invalid JPEG segment marker at 0x%X") % \
                                  (file.tell()))


#######################
#PNG
#######################

class InvalidPNG(InvalidImage): pass

class __PNG__(ImageMetrics):
    HEADER = construct.Const(construct.String('header',8),
                       '89504e470d0a1a0a'.decode('hex'))
    CHUNK_HEADER = construct.Struct('chunk',
                              construct.UBInt32('length'),
                              construct.String('type',4))
    CHUNK_FOOTER = construct.Struct('crc32',
                              construct.UBInt32('crc'))

    IHDR = construct.Struct('IHDR',
                      construct.UBInt32('width'),
                      construct.UBInt32('height'),
                      construct.Byte('bit_depth'),
                      construct.Byte('color_type'),
                      construct.Byte('compression_method'),
                      construct.Byte('filter_method'),
                      construct.Byte('interlace_method'))

    def __init__(self, width, height, bits_per_pixel, color_count):
        ImageMetrics.__init__(self, width, height, bits_per_pixel, color_count,
                              u'image/png')

    @classmethod
    def parse(cls, file):
        ihdr = None
        plte = None

        try:
            header = cls.HEADER.parse_stream(file)

            chunk_header = cls.CHUNK_HEADER.parse_stream(file)
            data = file.read(chunk_header.length)
            chunk_footer = cls.CHUNK_FOOTER.parse_stream(file)
            while (chunk_header.type != 'IEND'):
                if (chunk_header.type == 'IHDR'):
                    ihdr = cls.IHDR.parse(data)
                elif (chunk_header.type == 'PLTE'):
                    plte = data

                chunk_header = cls.CHUNK_HEADER.parse_stream(file)
                data = file.read(chunk_header.length)
                chunk_footer = cls.CHUNK_FOOTER.parse_stream(file)

            if (ihdr.color_type == 0):   #grayscale
                bits_per_pixel = ihdr.bit_depth
                color_count = 0
            elif (ihdr.color_type == 2): #RGB
                bits_per_pixel = ihdr.bit_depth * 3
                color_count = 0
            elif (ihdr.color_type == 3): #palette
                bits_per_pixel = 8
                if ((len(plte) % 3) != 0):
                    raise InvalidPNG(_(u'Invalid PLTE chunk length'))
                else:
                    color_count = len(plte) / 3
            elif (ihdr.color_type == 4): #grayscale + alpha
                bits_per_pixel = ihdr.bit_depth * 2
                color_count = 0
            elif (ihdr.color_type == 6): #RGB + alpha
                bits_per_pixel = ihdr.bit_depth * 4
                color_count = 0

            return __PNG__(ihdr.width,ihdr.height,bits_per_pixel,color_count)
        except construct.ConstError:
            raise InvalidPNG(_(u'Invalid PNG'))

#######################
#BMP
#######################

class InvalidBMP(InvalidImage): pass

class __BMP__(ImageMetrics):
    HEADER = construct.Struct('bmp_header',
                        construct.Const(construct.String('magic_number',2),'BM'),
                        construct.ULInt32('file_size'),
                        construct.ULInt16('reserved1'),
                        construct.ULInt16('reserved2'),
                        construct.ULInt32('bitmap_data_offset'))

    INFORMATION = construct.Struct('bmp_information',
                             construct.ULInt32('header_size'),
                             construct.ULInt32('width'),
                             construct.ULInt32('height'),
                             construct.ULInt16('color_planes'),
                             construct.ULInt16('bits_per_pixel'),
                             construct.ULInt32('compression_method'),
                             construct.ULInt32('image_size'),
                             construct.ULInt32('horizontal_resolution'),
                             construct.ULInt32('vertical_resolution'),
                             construct.ULInt32('colors_used'),
                             construct.ULInt32('important_colors_used'))

    def __init__(self, width, height, bits_per_pixel, color_count):
        ImageMetrics.__init__(self, width, height, bits_per_pixel, color_count,
                              u'image/x-ms-bmp')

    @classmethod
    def parse(cls, file):
        try:
            header = cls.HEADER.parse_stream(file)
            information = cls.INFORMATION.parse_stream(file)

            return __BMP__(information.width, information.height,
                           information.bits_per_pixel,
                           information.colors_used)

        except construct.ConstError:
            raise InvalidBMP(_(u'Invalid BMP'))

#######################
#GIF
#######################

class InvalidGIF(InvalidImage): pass

class __GIF__(ImageMetrics):
    HEADER = construct.Struct('header',
                        construct.Const(construct.String('gif',3),'GIF'),
                        construct.String('version',3))

    SCREEN_DESCRIPTOR = construct.Struct('logical_screen_descriptor',
                                   construct.ULInt16('width'),
                                   construct.ULInt16('height'),
                                   construct.Embed(
        construct.BitStruct('packed_fields',
                      construct.Flag('global_color_table'),
                      construct.Bits('color_resolution',3),
                      construct.Flag('sort'),
                      construct.Bits('global_color_table_size',3))),
                                   construct.Byte('background_color_index'),
                                   construct.Byte('pixel_aspect_ratio'))

    def __init__(self, width, height, color_count):
        ImageMetrics.__init__(self, width, height, 8, color_count, u'image/gif')

    @classmethod
    def parse(cls, file):
        try:
            header = cls.HEADER.parse_stream(file)
            descriptor = cls.SCREEN_DESCRIPTOR.parse_stream(file)

            return __GIF__(descriptor.width, descriptor.height,
                           2 ** (descriptor.global_color_table_size + 1))
        except construct.ConstError:
            raise InvalidGIF(_(u'Invalid GIF'))

#######################
#TIFF
#######################

class InvalidTIFF(InvalidImage): pass

class __TIFF__(ImageMetrics):
    HEADER = construct.Struct('header',
                        construct.String('byte_order',2),
                        construct.Switch('order',
                                   lambda ctx: ctx['byte_order'],
                                   {"II":construct.Embed(
        construct.Struct('little_endian',
                   construct.Const(construct.ULInt16('version'),42),
                   construct.ULInt32('offset'))),
                                    "MM":construct.Embed(
        construct.Struct('big_endian',
                   construct.Const(construct.UBInt16('version'),42),
                   construct.UBInt32('offset')))}))

    L_IFD = construct.Struct('ifd',
                       construct.PrefixedArray(
        length_field=construct.ULInt16('length'),
        subcon=construct.Struct('tags',
                          construct.ULInt16('id'),
                          construct.ULInt16('type'),
                          construct.ULInt32('count'),
                          construct.ULInt32('offset'))),
                       construct.ULInt32('next'))

    B_IFD = construct.Struct('ifd',
                       construct.PrefixedArray(
        length_field=construct.UBInt16('length'),
        subcon=construct.Struct('tags',
                          construct.UBInt16('id'),
                          construct.UBInt16('type'),
                          construct.UBInt32('count'),
                          construct.UBInt32('offset'))),
                       construct.UBInt32('next'))

    def __init__(self, width, height, bits_per_pixel, color_count):
        ImageMetrics.__init__(self, width, height,
                              bits_per_pixel, color_count,
                              u'image/tiff')

    @classmethod
    def b_tag_value(cls, file, tag):
        subtype = {1:construct.Byte("data"),
                   2:construct.CString("data"),
                   3:construct.UBInt16("data"),
                   4:construct.UBInt32("data"),
                   5:construct.Struct("data",
                                construct.UBInt32("high"),
                                construct.UBInt32("low"))}[tag.type]


        data = construct.StrictRepeater(tag.count,
                                  subtype)
        if ((tag.type != 2) and (data.sizeof() <= 4)):
            return tag.offset
        else:
            file.seek(tag.offset,0)
            return data.parse_stream(file)

    @classmethod
    def l_tag_value(cls, file, tag):
        subtype = {1:construct.Byte("data"),
                   2:construct.CString("data"),
                   3:construct.ULInt16("data"),
                   4:construct.ULInt32("data"),
                   5:construct.Struct("data",
                                construct.ULInt32("high"),
                                construct.ULInt32("low"))}[tag.type]


        data = construct.StrictRepeater(tag.count,
                                  subtype)
        if ((tag.type != 2) and (data.sizeof() <= 4)):
            return tag.offset
        else:
            file.seek(tag.offset,0)
            return data.parse_stream(file)

    @classmethod
    def parse(cls, file):
        width = 0
        height = 0
        bits_per_sample = 0
        color_count = 0

        try:
            header = cls.HEADER.parse_stream(file)
            if (header.byte_order == 'II'):
                IFD = cls.L_IFD
                tag_value = cls.l_tag_value
            elif (header.byte_order == 'MM'):
                IFD = cls.B_IFD
                tag_value = cls.b_tag_value
            else:
                raise InvalidTIFF(_(u'Invalid byte order'))

            file.seek(header.offset,0)

            ifd = IFD.parse_stream(file)

            while (True):
                for tag in ifd.tags:
                    if (tag.id == 0x0100):
                        width = tag_value(file,tag)
                    elif (tag.id == 0x0101):
                        height = tag_value(file,tag)
                    elif (tag.id == 0x0102):
                        try:
                            bits_per_sample = sum(tag_value(file,tag))
                        except TypeError:
                            bits_per_sample = tag_value(file,tag)
                    elif (tag.id == 0x0140):
                        color_count = tag.count / 3
                    else:
                        pass

                if (ifd.next == 0x00):
                    break
                else:
                    file.seek(ifd.next,0)
                    ifd = IFD.parse_stream(file)

            return __TIFF__(width,height,bits_per_sample,color_count)
        except construct.ConstError:
            raise InvalidTIFF(_(u'Invalid TIFF'))


#returns True if we have the capability to thumbnail images
#False if not
def can_thumbnail():
    try:
        import Image as PIL_Image
        return True
    except ImportError:
        return False

#returns a list of available thumbnail image formats
def thumbnail_formats():
    import Image as PIL_Image
    import cStringIO

    #performing a dummy save seeds PIL_Image.SAVE with possible save types
    PIL_Image.new("RGB",(1,1)).save(cStringIO.StringIO(),"bmp")

    return PIL_Image.SAVE.keys()

#takes a string of raw image data
#along with width and height integers
#and an image format string
#returns a new image data string in the given format
#no larger than the given width and height
def thumbnail_image(image_data, width, height, format):
    import cStringIO
    import Image as PIL_Image
    import ImageFile as PIL_ImageFile

    PIL_ImageFile.MAXBLOCK = 0x100000

    img = PIL_Image.open(cStringIO.StringIO(image_data))
    img.thumbnail((width,height),PIL_Image.ANTIALIAS)
    output = cStringIO.StringIO()

    if (format.upper() == 'JPEG'):
        #PIL's default JPEG save quality isn't too great
        #so it's best to add a couple of optimizing parameters
        #since this is a common case
        img.save(output,'JPEG',quality=90,optimize=True)
    else:
        img.save(output,format)

    return output.getvalue()

