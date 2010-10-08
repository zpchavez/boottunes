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
#import construct as Con

#M4A atoms are typically laid on in the file as follows:
# ftyp
# mdat
# moov/
# +mvhd
# +iods
# +trak/
# +-tkhd
# +-mdia/
# +--mdhd
# +--hdlr
# +--minf/
# +---smhd
# +---dinf/
# +----dref
# +---stbl/
# +----stsd
# +----stts
# +----stsz
# +----stsc
# +----stco
# +----ctts
# +udta/
# +-meta
#
#Where atoms ending in / are container atoms and the rest are leaf atoms.
#'mdat' is where the file's audio stream is stored
#the rest are various bits of metadata

def VersionLength(name):
    return construct.IfThenElse(name,
                          lambda ctx: ctx["version"] == 0,
                          construct.UBInt32(None),
                          construct.UBInt64(None))

class AtomAdapter(construct.Adapter):
    def _encode(self, obj, context):
        obj.size = len(obj.data) + 8
        return obj

    def _decode(self, obj, context):
        del(obj.size)
        return obj

def Atom(name):
    return AtomAdapter(construct.Struct(
            name,
            construct.UBInt32("size"),
            construct.String("type",4),
            construct.String("data",lambda ctx: ctx["size"] - 8)))

class AtomListAdapter(construct.Adapter):
    ATOM_LIST = construct.GreedyRepeater(Atom("atoms"))

    def _encode(self, obj, context):
        obj.data = self.ATOM_LIST.build(obj.data)
        return obj

    def _decode(self, obj, context):
        obj.data = self.ATOM_LIST.parse(obj.data)
        return obj

def AtomContainer(name):
    return AtomListAdapter(Atom(name))

#wraps around an existing sub_atom and automatically appends/removes header
#during build/parse operations
#this should probably be an adapter, but it does seem to work okay
class AtomWrapper(construct.Struct):
    def __init__(self, atom_name, sub_atom):
        construct.Struct.__init__(self,atom_name)
        self.atom_name = atom_name
        self.sub_atom = sub_atom
        self.header = construct.Struct(atom_name,
                                 construct.UBInt32("size"),
                                 construct.Const(construct.String("type",4),atom_name))

    def _parse(self, stream, context):
        header = self.header.parse_stream(stream)
        return self.sub_atom.parse_stream(stream)

    def _build(self, obj, stream, context):
        data = self.sub_atom.build(obj)
        stream.write(self.header.build(construct.Container(type=self.atom_name,
                                                     size=len(data) + 8)))
        stream.write(data)

    def _sizeof(self, context):
        return self.sub_atom.sizeof(context) + 8



ATOM_FTYP = construct.Struct("ftyp",
                        construct.String("major_brand",4),
                        construct.UBInt32("major_brand_version"),
                        construct.GreedyRepeater(construct.String("compatible_brands",4)))

ATOM_MVHD = construct.Struct("mvhd",
                       construct.Byte("version"),
                       construct.String("flags",3),
                       VersionLength("created_mac_UTC_date"),
                       VersionLength("modified_mac_UTC_date"),
                       construct.UBInt32("time_scale"),
                       VersionLength("duration"),
                       construct.UBInt32("playback_speed"),
                       construct.UBInt16("user_volume"),
                       construct.Padding(10),
                       construct.Struct("windows",
                                  construct.UBInt32("geometry_matrix_a"),
                                  construct.UBInt32("geometry_matrix_b"),
                                  construct.UBInt32("geometry_matrix_u"),
                                  construct.UBInt32("geometry_matrix_c"),
                                  construct.UBInt32("geometry_matrix_d"),
                                  construct.UBInt32("geometry_matrix_v"),
                                  construct.UBInt32("geometry_matrix_x"),
                                  construct.UBInt32("geometry_matrix_y"),
                                  construct.UBInt32("geometry_matrix_w")),
                       construct.UBInt64("quicktime_preview"),
                       construct.UBInt32("quicktime_still_poster"),
                       construct.UBInt64("quicktime_selection_time"),
                       construct.UBInt32("quicktime_current_time"),
                       construct.UBInt32("next_track_id"))

ATOM_IODS = construct.Struct("iods",
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.Byte("type_tag"),
                       construct.Switch("descriptor",
                                  lambda ctx: ctx.type_tag,
                                  {0x10: construct.Struct(
                None,
                construct.StrictRepeater(3,construct.Byte("extended_descriptor_type")),
                construct.Byte("descriptor_type_length"),
                construct.UBInt16("OD_ID"),
                construct.Byte("OD_profile"),
                construct.Byte("scene_profile"),
                construct.Byte("audio_profile"),
                construct.Byte("video_profile"),
                construct.Byte("graphics_profile")),
                                   0x0E: construct.Struct(
                None,
                construct.StrictRepeater(3,construct.Byte("extended_descriptor_type")),
                construct.Byte("descriptor_type_length"),
                construct.String("track_id",4))}))

ATOM_TKHD = construct.Struct("tkhd",
                       construct.Byte("version"),
                       construct.BitStruct("flags",
                                     construct.Padding(20),
                                     construct.Flag("TrackInPoster"),
                                     construct.Flag("TrackInPreview"),
                                     construct.Flag("TrackInMovie"),
                                     construct.Flag("TrackEnabled")),
                       VersionLength("created_mac_UTC_date"),
                       VersionLength("modified_mac_UTC_date"),
                       construct.UBInt32("track_id"),
                       construct.Padding(4),
                       VersionLength("duration"),
                       construct.Padding(8),
                       construct.UBInt16("video_layer"),
                       construct.UBInt16("quicktime_alternate"),
                       construct.UBInt16("volume"),
                       construct.Padding(2),
                       construct.Struct("video",
                                  construct.UBInt32("geometry_matrix_a"),
                                  construct.UBInt32("geometry_matrix_b"),
                                  construct.UBInt32("geometry_matrix_u"),
                                  construct.UBInt32("geometry_matrix_c"),
                                  construct.UBInt32("geometry_matrix_d"),
                                  construct.UBInt32("geometry_matrix_v"),
                                  construct.UBInt32("geometry_matrix_x"),
                                  construct.UBInt32("geometry_matrix_y"),
                                  construct.UBInt32("geometry_matrix_w")),
                       construct.UBInt32("video_width"),
                       construct.UBInt32("video_height"))

ATOM_MDHD = construct.Struct("mdhd",
                       construct.Byte("version"),
                       construct.String("flags",3),
                       VersionLength("created_mac_UTC_date"),
                       VersionLength("modified_mac_UTC_date"),
                       construct.UBInt32("time_scale"),
                       VersionLength("duration"),
                       construct.BitStruct("languages",
                                     construct.Padding(1),
                                     construct.StrictRepeater(3,
                                                        construct.Bits("language",5))),
                       construct.UBInt16("quicktime_quality"))


ATOM_HDLR = construct.Struct("hdlr",
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.String("quicktime_type",4),
                       construct.String("subtype",4),
                       construct.String("quicktime_manufacturer",4),
                       construct.UBInt32("quicktime_component_reserved_flags"),
                       construct.UBInt32("quicktime_component_reserved_flags_mask"),
                       construct.PascalString("component_name"),
                       construct.Padding(1))

ATOM_SMHD = construct.Struct('smhd',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.String("audio_balance",2),
                       construct.Padding(2))

ATOM_DREF = construct.Struct('dref',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.PrefixedArray(
        length_field=construct.UBInt32("num_references"),
        subcon=Atom("references")))


ATOM_STSD = construct.Struct('stsd',
                       construct.Byte("version"),
                       construct.String("flags",3),
                        construct.PrefixedArray(
        length_field=construct.UBInt32("num_descriptions"),
        subcon=Atom("descriptions")))

ATOM_MP4A = construct.Struct("mp4a",
                       construct.Padding(6),
                       construct.UBInt16("reference_index"),
                       construct.UBInt16("quicktime_audio_encoding_version"),
                       construct.UBInt16("quicktime_audio_encoding_revision"),
                       construct.String("quicktime_audio_encoding_vendor",4),
                       construct.UBInt16("channels"),
                       construct.UBInt16("sample_size"),
                       construct.UBInt16("audio_compression_id"),
                       construct.UBInt16("quicktime_audio_packet_size"),
                       construct.String("sample_rate",4))

#out of all this mess, the only interesting bits are the _bit_rate fields
#and (maybe) the buffer_size
#everything else is a constant of some kind as far as I can tell
ATOM_ESDS = construct.Struct("esds",
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.Byte("ES_descriptor_type"),
                       construct.StrictRepeater(
        3,construct.Byte("extended_descriptor_type_tag")),
                       construct.Byte("descriptor_type_length"),
                       construct.UBInt16("ES_ID"),
                       construct.Byte("stream_priority"),
                       construct.Byte("decoder_config_descriptor_type"),
                       construct.StrictRepeater(
        3,construct.Byte("extended_descriptor_type_tag2")),
                       construct.Byte("descriptor_type_length2"),
                       construct.Byte("object_ID"),
                       construct.Embed(
        construct.BitStruct(None,construct.Bits("stream_type",6),
                      construct.Flag("upstream_flag"),
                      construct.Flag("reserved_flag"),
                      construct.Bits("buffer_size",24))),
                       construct.UBInt32("maximum_bit_rate"),
                       construct.UBInt32("average_bit_rate"),
                       construct.Byte('decoder_specific_descriptor_type3'),
                       construct.StrictRepeater(
        3,construct.Byte("extended_descriptor_type_tag2")),
                       construct.PrefixedArray(
        length_field=construct.Byte("ES_header_length"),
        subcon=construct.Byte("ES_header_start_codes")),
                       construct.Byte("SL_config_descriptor_type"),
                       construct.StrictRepeater(
        3,construct.Byte("extended_descriptor_type_tag3")),
                       construct.Byte("descriptor_type_length3"),
                       construct.Byte("SL_value"))


ATOM_STTS = construct.Struct('stts',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.PrefixedArray(length_field=construct.UBInt32("total_counts"),
                                     subcon=construct.Struct("frame_size_counts",
                                                       construct.UBInt32("frame_count"),
                                                       construct.UBInt32("duration"))))


ATOM_STSZ = construct.Struct('stsz',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.UBInt32("block_byte_size"),
                       construct.PrefixedArray(length_field=construct.UBInt32("total_sizes"),
                                         subcon=construct.UBInt32("block_byte_sizes")))


ATOM_STSC = construct.Struct('stsc',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.PrefixedArray(
        length_field=construct.UBInt32("entry_count"),
        subcon=construct.Struct("block",
                          construct.UBInt32("first_chunk"),
                          construct.UBInt32("samples_per_chunk"),
                          construct.UBInt32("sample_description_index"))))

ATOM_STCO = construct.Struct('stco',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.PrefixedArray(
        length_field=construct.UBInt32("total_offsets"),
        subcon=construct.UBInt32("offset")))

ATOM_CTTS = construct.Struct('ctts',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.PrefixedArray(
        length_field=construct.UBInt32("entry_count"),
        subcon=construct.Struct("sample",
                          construct.UBInt32("sample_count"),
                          construct.UBInt32("sample_offset"))))

ATOM_META = construct.Struct('meta',
                       construct.Byte("version"),
                       construct.String("flags",3),
                       construct.GreedyRepeater(Atom("atoms")))

ATOM_ILST = construct.GreedyRepeater(AtomContainer('ilst'))

ATOM_TRKN = construct.Struct('trkn',
                       construct.Padding(2),
                       construct.UBInt16('track_number'),
                       construct.UBInt16('total_tracks'),
                       construct.Padding(2))

ATOM_DISK = construct.Struct('disk',
                       construct.Padding(2),
                       construct.UBInt16('disk_number'),
                       construct.UBInt16('total_disks'))
