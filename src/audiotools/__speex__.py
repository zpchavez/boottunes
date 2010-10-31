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


from audiotools import AudioFile,InvalidFile,PCMReader,PCMConverter,construct,transfer_data,transfer_framelist_data,subprocess,BIN,cStringIO,os,ignore_sigint,EncodingError,DecodingError,ChannelMask
from __vorbis__ import *

#######################
#Speex File
#######################

class UnframedVorbisComment(VorbisComment):
    VORBIS_COMMENT = construct.Struct("vorbis_comment",
                                construct.PascalString("vendor_string",
                                                 length_field=construct.ULInt32("length")),
                                construct.PrefixedArray(
        length_field=construct.ULInt32("length"),
        subcon=construct.PascalString("value",
                                length_field=construct.ULInt32("length"))))

class SpeexAudio(VorbisAudio):
    SUFFIX = "spx"
    NAME = SUFFIX
    DEFAULT_COMPRESSION = "8"
    COMPRESSION_MODES = tuple([str(i) for i in range(0,11)])
    BINARIES = ("speexenc","speexdec")

    SPEEX_HEADER = construct.Struct('speex_header',
                              construct.String('speex_string',8),
                              construct.String('speex_version',20),
                              construct.ULInt32('speex_version_id'),
                              construct.ULInt32('header_size'),
                              construct.ULInt32('sampling_rate'),
                              construct.ULInt32('mode'),
                              construct.ULInt32('mode_bitstream_version'),
                              construct.ULInt32('channels'),
                              construct.ULInt32('bitrate'),
                              construct.ULInt32('frame_size'),
                              construct.ULInt32('vbr'),
                              construct.ULInt32('frame_per_packet'),
                              construct.ULInt32('extra_headers'),
                              construct.ULInt32('reserved1'),
                              construct.ULInt32('reserved2'))

    def __init__(self, filename):
        AudioFile.__init__(self, filename)
        self.__read_metadata__()

    @classmethod
    def is_type(cls, file):
        header = file.read(0x23)

        return (header.startswith('OggS') and
                header[0x1C:0x23] == 'Speex  ')

    def __read_metadata__(self):
        f = OggStreamReader(file(self.filename,"rb"))
        packets = f.packets()
        try:
            #first read the Header packet
            header = SpeexAudio.SPEEX_HEADER.parse(packets.next())

            self.__sample_rate__ = header.sampling_rate
            self.__channels__ = header.channels

            #the read the Comment packet
            comment_packet = packets.next()

            self.comment = UnframedVorbisComment.VORBIS_COMMENT.parse(
                comment_packet)
        finally:
            del(packets); f.close(); del(f)

    def to_pcm(self):
        devnull = file(os.devnull,'ab')
        sub = subprocess.Popen([BIN['speexdec'],self.filename,'-'],
                               stdout=subprocess.PIPE,
                               stderr=devnull)
        return PCMReader(
            sub.stdout,
            sample_rate=self.sample_rate(),
            channels=self.channels(),
            channel_mask=int(ChannelMask.from_channels(self.channels())),
            bits_per_sample=self.bits_per_sample(),
            process=sub)

    @classmethod
    def from_pcm(cls, filename, pcmreader, compression=None):
        import bisect

        if (compression not in cls.COMPRESSION_MODES):
            compression = cls.DEFAULT_COMPRESSION

        if ((pcmreader.bits_per_sample not in (8,16)) or
            (pcmreader.channels > 2) or
            (pcmreader.sample_rate not in (8000,16000,32000,44100))):
            pcmreader = PCMConverter(
                pcmreader,
                sample_rate=[8000,8000,16000,32000,44100][bisect.bisect(
                    [8000,16000,32000,44100],pcmreader.sample_rate)],
                channels=min(pcmreader.channels,2),
                channel_mask=ChannelMask.from_channels(min(pcmreader.channels,2)),
                bits_per_sample=min(pcmreader.bits_per_sample,16))


        BITS_PER_SAMPLE = {8:['--8bit'],
                           16:['--16bit']}[pcmreader.bits_per_sample]

        CHANNELS = {1:[],2:['--stereo']}[pcmreader.channels]

        devnull = file(os.devnull,"ab")

        sub = subprocess.Popen([BIN['speexenc'],
                                '--quality',str(compression),
                                '--rate',str(pcmreader.sample_rate),
                                '--le'] + \
                               BITS_PER_SAMPLE + \
                               CHANNELS + \
                               ['-',filename],
                               stdin=subprocess.PIPE,
                               stderr=devnull,
                               preexec_fn=ignore_sigint)

        transfer_framelist_data(pcmreader,sub.stdin.write)
        try:
            pcmreader.close()
        except DecodingError:
            raise EncodingError()
        sub.stdin.close()
        result = sub.wait()
        devnull.close()

        if (result == 0):
            return SpeexAudio(filename)
        else:
            raise EncodingError(BIN['speexenc'])

    def set_metadata(self, metadata):
        comment = VorbisComment.converted(metadata)

        if (comment is None): return

        reader = OggStreamReader(file(self.filename,'rb'))
        new_file = cStringIO.StringIO()
        writer = OggStreamWriter(new_file)

        pages = reader.pages()

        #transfer our old header
        (header_page,header_data) = pages.next()
        writer.write_page(header_page,header_data)

        #skip the existing comment packet
        (page,data) = pages.next()
        while (page.segment_lengths[-1] == 255):
            (page,data) = pages.next()

        #write the pages for our new comment packet
        comment_pages = OggStreamWriter.build_pages(
            0,
            header_page.bitstream_serial_number,
            header_page.page_sequence_number + 1,
            comment.build())

        for (page,data) in comment_pages:
            writer.write_page(page,data)

        #write the rest of the pages, re-sequenced and re-checksummed
        sequence_number = comment_pages[-1][0].page_sequence_number + 1
        for (i,(page,data)) in enumerate(pages):
            page.page_sequence_number = i + sequence_number
            page.checksum = OggStreamReader.calculate_ogg_checksum(page,data)
            writer.write_page(page,data)

        reader.close()

        #re-write the file with our new data in "new_file"
        f = file(self.filename,"wb")
        f.write(new_file.getvalue())
        f.close()
        writer.close()

        self.__read_metadata__()

    @classmethod
    def can_add_replay_gain(cls):
        return False
