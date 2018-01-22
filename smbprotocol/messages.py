import struct

from smbprotocol.structure import BytesField, DateTimeField, EnumField, \
    FlagField, IntField, ListField, Structure, StructureField, UuidField
from smbprotocol.constants import Capabilities, Ciphers, CloseFlags, \
    Commands, CreateAction, CreateContextName, CreateDisposition, \
    CreateOptions, CtlCode, Dialects, FileAttributes, FileFlags, \
    HashAlgorithms, ImpersonationLevel, IOCTLFlags, NegotiateContextType, \
    RequestedOplockLevel, SecurityMode, SessionFlags, ShareAccess, \
    ShareCapabilities, ShareFlags, ShareType, Smb1Flags2, Smb2Flags, TreeFlags

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


# value lambda is executed when we call .pack()
# size lambda is executed when .set_value()
# None is \x00 * size
class DirectTCPPacket(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.1 Transport
    The Directory TCP transport packet header MUST have the following
    structure.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('stream_protocol_length', IntField(
                size=4,
                byte_order='>',
                default=lambda s: len(s['smb2_message']),
            )),
            ('smb2_message', BytesField(
                size=lambda s: s['stream_protocol_length'].get_value(),
            )),
        ])
        super(DirectTCPPacket, self).__init__()


class SMB1PacketHeader(Structure):
    """
    [MS-SMB] v46.0 2017-0-01

    2.2.3.1 SMB Header Extensions
    Used in the initial negotiation process, the SMBv1 header must be sent
    with the SMBv1 Negotiate Request packet in order to determine if the server
    supports SMBv2+.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('protocol', BytesField(
                size=4,
                default=b'\xffSMB',
            )),
            ('command', IntField(size=1)),
            ('status', IntField(size=4)),
            ('flags', IntField(size=1)),
            ('flags2', FlagField(
                size=2,
                flag_type=Smb1Flags2,
            )),
            ('pid_high', IntField(size=2)),
            ('security_features', IntField(size=8)),
            ('reserved', IntField(size=2)),
            ('tid', IntField(size=2)),
            ('pid_low', IntField(size=2)),
            ('uid', IntField(size=2)),
            ('mid', IntField(size=2)),
            ('data', StructureField(
                structure_type=SMB1NegotiateRequest
            ))
        ])
        super(SMB1PacketHeader, self).__init__()


class SMB2PacketHeader(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.1.2 SMB2 Packet Header - SYNC
    The header of all SMBv2 Protocol requests and responses. This is the SYNC
    form of the header is is used for all server responses and on client
    requests if SMBv2 was negotiated. If SMBv3 was negotiated then
    SMB3PacketHeader is used on all client requests.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('protocol_id', BytesField(
                size=4,
                default=b'\xfeSMB',
            )),
            ('structure_size', IntField(
                size=2,
                default=64,
            )),
            ('credit_charge', IntField(size=2)),
            ('status', IntField(size=4)),
            ('command', EnumField(
                size=2,
                enum_type=Commands
            )),
            ('credit', IntField(size=2)),
            ('flags', FlagField(
                size=4,
                flag_type=Smb2Flags,
            )),
            ('next_command', IntField(size=4)),
            ('message_id', IntField(size=8)),
            ('reserved', IntField(size=4)),
            ('tree_id', IntField(size=4)),
            ('session_id', IntField(size=8)),
            ('signature', BytesField(
                size=16,
                default=b"\x00" * 16,
            )),
            ('data', BytesField()),
        ])
        super(SMB2PacketHeader, self).__init__()


class SMB3PacketHeader(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.1.2 SMB2 Packet Header - SYNC
    This is the same as SMB2PacketHeader except it contains the
    channel_sequence + reserved fields instead of status. This is used on all
    client requests if the Dialect negotiated is v3.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('protocol_id', BytesField(
                size=4,
                default=b"\xfeSMB",
            )),
            ('structure_size', IntField(
                size=2,
                default=64,
            )),
            ('credit_charge', IntField(size=2)),
            ('channel_sequence', IntField(size=2)),
            ('reserved', IntField(size=2)),
            ('command', EnumField(
                size=2,
                enum_type=Commands
            )),
            ('credit', IntField(size=2)),
            ('flags', FlagField(
                size=4,
                flag_type=Smb2Flags,
            )),
            ('next_command', IntField(size=4)),
            ('message_id', IntField(size=8)),
            ('process_id', IntField(size=4)),
            ('tree_id', IntField(size=4)),
            ('session_id', IntField(size=8)),
            ('signature', BytesField(
                size=16,
                default=b"\x00" * 16,
            )),
            ('data', BytesField()),
        ])
        super(SMB3PacketHeader, self).__init__()


class SMB2ErrorResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.2 SMB2 Error Response
    The SMB2 Error Response packet is sent by the server to respond to a
    request that has failed or encountered an error. This is only used in the
    SMB 3.1.1 dialect and this code won't decode values based on older versions
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=9,
            )),
            ('error_context_count', IntField(
                size=1,
                default=lambda s: len(s['error_data'].get_value()),
            )),
            ('reserved', IntField(size=1)),
            ('byte_count', IntField(
                size=4,
                default=lambda s: len(s['error_data']),
            )),
            ('error_data', ListField(
                size=lambda s: s['byte_count'].get_value(),
                list_count=lambda s: s['error_context_count'].get_value(),
                unpack_func=lambda s, d: self._error_data_value(s, d)
            )),
        ])
        super(SMB2ErrorResponse, self).__init__()

    def _error_data_value(self, structure, data):
        # parse raw bytes into a list we can iterate through
        # TODO: add code to parse data into a list
        return []


class SMB2ErrorContextResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.2.1 SMB2 ERROR Context Response
    For the SMB dialect 3.1.1, the server formats the error data as an array of
    SMB2 Error Context structures in the SMB2ErrorResponse message.

    """

    def __init__(self):
        self.fields = OrderedDict([
            ('error_data_length', IntField(
                size=4,
                default=lambda s: len(s['error_context_data']),
            )),
            ('error_id', IntField(size=4)),
            ('error_context_data', BytesField(
                size=lambda s: s['error_data_length'].get_value(),
            )),
        ])
        super(SMB2ErrorContextResponse, self).__init__()


class SMB1NegotiateRequest(Structure):
    """
    [MS-CIFS] v27.0 2017-06-01

    2.2.4.52 SMB_COM_NEGOTIATE (0x72)
    The command is used to initial an SMB connection between the client and
    the server. This is used only in the initial negotiation process to
    determine whether SMBv2+ is supported on the server.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('word_count', IntField(size=1)),
            ('byte_count', IntField(
                size=2,
                default=lambda s: len(s['dialects']),
            )),
            ('dialects', BytesField(
                size=lambda s: s['byte_count'].get_value(),
            )),
        ])
        super(SMB1NegotiateRequest, self).__init__()


class SMB2NegotiateRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.3 SMB2 Negotiate Request
    The SMB2 NEGOTIATE Request packet is used by the client to notify the
    server what dialects of the SMB2 Protocol the client understands. This is
    only used if the client explicitly sets the Dialect to use to a version
    less than 3.1.1. Dialect 3.1.1 added support for negotiate_context and
    SMB3NegotiateRequest should be used to support that.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=36,
            )),
            ('dialect_count', IntField(
                size=2,
                default=lambda s: len(s['dialects'].get_value()),
            )),
            ('security_mode', FlagField(
                size=2,
                flag_type=SecurityMode
            )),
            ('reserved', IntField(size=2)),
            ('capabilities', FlagField(
                size=4,
                flag_type=Capabilities,
            )),
            ('client_guid', UuidField()),
            ('client_start_time', IntField(size=8)),
            ('dialects', ListField(
                size=lambda s: s['dialect_count'].get_value() * 2,
                list_count=lambda s: s['dialect_count'].get_value(),
                list_type=EnumField(size=2, enum_type=Dialects),
            )),
        ])

        super(SMB2NegotiateRequest, self).__init__()


class SMB3NegotiateRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.3 SMB2 Negotiate Request
    Like SMB2NegotiateRequest but with support for setting a list of
    Negotiate Context values. This is used by default and is for Dialects 3.1.1
    or greater.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=36,
            )),
            ('dialect_count', IntField(
                size=2,
                default=lambda s: len(s['dialects'].get_value()),
            )),
            ('security_mode', FlagField(
                size=2,
                flag_type=SecurityMode,
            )),
            ('reserved', IntField(size=2)),
            ('capabilities', FlagField(
                size=4,
                flag_type=Capabilities,
            )),
            ('client_guid', UuidField()),
            ('negotiate_context_offset', IntField(
                size=4,
                default=lambda s: self._negotiate_context_offset_value(s),
            )),
            ('negotiate_context_count', IntField(
                size=2,
                default=lambda s: len(s['negotiate_context_list'].get_value()),
            )),
            ('reserved2', IntField(size=2)),
            ('dialects', ListField(
                size=lambda s: s['dialect_count'].get_value() * 2,
                list_count=lambda s: s['dialect_count'].get_value(),
                list_type=EnumField(size=2, enum_type=Dialects),
            )),
            ('padding', BytesField(
                size=lambda s: self._padding_size(s),
                default=lambda s: b"\x00" * self._padding_size(s),
            )),
            ('negotiate_context_list', ListField(
                list_count=lambda s: s['negotiate_context_count'].get_value(),
                unpack_func=lambda s, d: self._negotiate_context_list(s, d),
            )),
        ])
        super(SMB3NegotiateRequest, self).__init__()

    def _negotiate_context_offset_value(self, structure):
        # The offset from the beginning of the SMB2 header to the first, 8-byte
        # aligned, negotiate context
        header_size = 64
        negotiate_size = structure['structure_size'].get_value()
        dialect_size = len(structure['dialects'])
        padding_size = self._padding_size(structure)
        return header_size + negotiate_size + dialect_size + padding_size

    def _padding_size(self, structure):
        # Padding between the end of the buffer value and the first Negotiate
        # context value so that the first value is 8-byte aligned. Padding is
        # 4 is there are no dialects specified
        mod = (structure['dialect_count'].get_value() * 2) % 8
        return 0 if mod == 0 else mod

    def _negotiate_context_list(self, structure, data):
        context_count = structure['negotiate_context_count'].get_value()
        context_list = []
        for idx in range(0, context_count):
            field, data = self._parse_negotiate_context_entry(data, idx)
            context_list.append(field)

        return context_list

    def _parse_negotiate_context_entry(self, data, idx):
        data_length = struct.unpack("<H", data[2:4])[0]
        negotiate_context = SMB2NegotiateContextRequest()
        negotiate_context.unpack(data[:data_length + 8])
        return negotiate_context, data[8 + data_length:]


class SMB2NegotiateContextRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.3.1 SMB2 NEGOTIATE_CONTEXT Request Values
    The SMB2_NEGOTIATE_CONTEXT structure is used by the SMB2 NEGOTIATE Request
    and the SMB2 NEGOTIATE Response to encode additional properties.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('context_type', EnumField(
                size=2,
                enum_type=NegotiateContextType,
            )),
            ('data_length', IntField(
                size=2,
                default=lambda s: len(s['data'].get_value()),
            )),
            ('reserved', IntField(size=4)),
            ('data', StructureField(
                size=lambda s: s['data_length'].get_value(),
                structure_type=lambda s: self._data_structure_type(s)
            )),
            # not actually a field but each list entry must start at the 8 byte
            # alignment
            ('padding', BytesField(
                size=lambda s: self._padding_size(s),
                default=lambda s: b"\x00" * self._padding_size(s),
            ))
        ])
        super(SMB2NegotiateContextRequest, self).__init__()

    def _data_structure_type(self, structure):
        con_type = structure['context_type'].get_value()
        if con_type == \
                NegotiateContextType.SMB2_PREAUTH_INTEGRITY_CAPABILITIES:
            return SMB2PreauthIntegrityCapabilities
        elif con_type == NegotiateContextType.SMB2_ENCRYPTION_CAPABILITIES:
            return SMB2EncryptionCapabilities

    def _padding_size(self, structure):
        data_size = len(structure['data'])
        return 8 - data_size if data_size <= 8 else 8 - (data_size % 8)


class SMB2PreauthIntegrityCapabilities(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.3.1.1 SMB2_PREAUTH_INTEGRITY_CAPABILITIES
    The SMB2_PREAUTH_INTEGRITY_CAPABILITIES context is specified in an SMB2
    NEGOTIATE request by the client to indicate which preauthentication
    integrity hash algorithms it supports and to optionally supply a
    preauthentication integrity hash salt value.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('hash_algorithm_count', IntField(
                size=2,
                default=lambda s: len(s['hash_algorithms'].get_value()),
            )),
            ('salt_length', IntField(
                size=2,
                default=lambda s: len(s['salt']),
            )),
            ('hash_algorithms', ListField(
                size=lambda s: s['hash_algorithm_count'].get_value() * 2,
                list_count=lambda s: s['hash_algorithm_count'].get_value(),
                list_type=EnumField(size=2, enum_type=HashAlgorithms),
            )),
            ('salt', BytesField(
                size=lambda s: s['salt_length'].get_value(),
            )),
        ])
        super(SMB2PreauthIntegrityCapabilities, self).__init__()


class SMB2EncryptionCapabilities(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.3.1.2 SMB2_ENCRYPTION_CAPABILITIES
    The SMB2_ENCRYPTION_CAPABILITIES context is specified in an SMB2 NEGOTIATE
    request by the client to indicate which encryption algorithms the client
    supports.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('cipher_count', IntField(
                size=2,
                default=lambda s: len(s['ciphers'].get_value()),
            )),
            ('ciphers', ListField(
                size=lambda s: s['cipher_count'].get_value() * 2,
                list_count=lambda s: s['cipher_count'].get_value(),
                list_type=EnumField(size=2, enum_type=Ciphers),
            )),
        ])
        super(SMB2EncryptionCapabilities, self).__init__()


class SMB2NegotiateResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.4 SMB2 NEGOTIATE Response
    The SMB2 NEGOTIATE Response packet is sent by the server to notify the
    client of the preferred common dialect.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=65,
            )),
            ('security_mode', FlagField(
                size=2,
                flag_type=SecurityMode,
            )),
            ('dialect_revision', EnumField(
                size=2,
                enum_type=Dialects,
            )),
            ('negotiate_context_count', IntField(
                size=2,
                default=lambda s: self._negotiate_context_count_value(s),
            )),
            ('server_guid', UuidField()),
            ('capabilities', FlagField(
                size=4,
                flag_type=Capabilities
            )),
            ('max_transact_size', IntField(size=4)),
            ('max_read_size', IntField(size=4)),
            ('max_write_size', IntField(size=4)),
            ('system_time', DateTimeField()),
            ('server_start_time', DateTimeField()),
            ('security_buffer_offset', IntField(
                size=2,
                default=128,  # (header size 64) + (structure size 64)
            )),
            ('security_buffer_length', IntField(
                size=2,
                default=lambda s: len(s['buffer'].get_value()),
            )),
            ('negotiate_context_offset', IntField(
                size=4,
                default=lambda s: self._negotiate_context_offset_value(s),
            )),
            ('buffer', BytesField(
                size=lambda s: s['security_buffer_length'].get_value(),
            )),
            ('padding', BytesField(
                size=lambda s: self._padding_size(s),
                default=lambda s: b"\x00" * self._padding_size(s),
            )),
            ('negotiate_context_list', ListField(
                list_count=lambda s: s['negotiate_context_count'].get_value(),
                unpack_func=lambda s, d:
                self._negotiate_context_list(s, d),
            )),
        ])
        super(SMB2NegotiateResponse, self).__init__()

    def _negotiate_context_count_value(self, structure):
        # If the dialect_revision is SMBv3.1.1, this field specifies the
        # number of negotiate contexts in negotiate_context_list; otherwise
        # this field must not be used and must be reserved (0).
        if structure['dialect_revision'].get_value() == Dialects.SMB_3_1_1:
            return len(structure['negotiate_context_list'].get_value())
        else:
            return None

    def _negotiate_context_offset_value(self, structure):
        # If the dialect_revision is SMBv3.1.1, this field specifies the offset
        # from the beginning of the SMB2 header to the first 8-byte
        # aligned negotiate context entry in negotiate_context_list; otherwise
        # this field must not be used and must be reserved (0).
        if structure['dialect_revision'].get_value() == Dialects.SMB_3_1_1:
            buffer_offset = structure['security_buffer_offset'].get_value()
            buffer_size = structure['security_buffer_length'].get_value()
            padding_size = self._padding_size(structure)
            return buffer_offset + buffer_size + padding_size
        else:
            return None

    def _padding_size(self, structure):
        # Padding between the end of the buffer value and the first Negotiate
        # context value so that the first value is 8-byte aligned. Padding is
        # not required if there are not negotiate contexts
        if structure['negotiate_context_count'].get_value() == 0:
            return 0

        mod = structure['security_buffer_length'].get_value() % 8
        return 0 if mod == 0 else 8 - mod

    def _negotiate_context_list(self, structure, data):
        context_count = structure['negotiate_context_count'].get_value()
        context_list = []
        for idx in range(0, context_count):
            field, data = self._parse_negotiate_context_entry(data)
            context_list.append(field)

        return context_list

    def _parse_negotiate_context_entry(self, data):
        data_length = struct.unpack("<H", data[2:4])[0]
        negotiate_context = SMB2NegotiateContextRequest()
        negotiate_context.unpack(data[:data_length + 8])
        padded_size = data_length % 8
        if padded_size != 0:
            padded_size = 8 - padded_size

        return negotiate_context, data[8 + data_length + padded_size:]


class SMB2SessionSetupRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.5 SMB2 SESSION_SETUP Request
    The SMB2 SESSION_SETUP Request packet is sent by the client to request a
    new authenticated session within a new or existing SMB 2 connection.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=25,
            )),
            ('flags', IntField(size=1)),
            ('security_mode', EnumField(
                size=1,
                enum_type=SecurityMode,
            )),
            ('capabilities', FlagField(
                size=4,
                flag_type=Capabilities,
            )),
            ('channel', IntField(size=4)),
            ('security_buffer_offset', IntField(
                size=2,
                default=88,  # (header size 64) + (response size 24)
            )),
            ('security_buffer_length', IntField(
                size=2,
                default=lambda s: len(s['buffer']),
            )),
            ('previous_session_id', IntField(size=8)),
            ('buffer', BytesField(
                size=lambda s: s['security_buffer_length'].get_value(),
            )),
        ])
        super(SMB2SessionSetupRequest, self).__init__()


class SMB2SessionSetupResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.6 SMB2 SESSION_SETUP Response
    The SMB2 SESSION_SETUP Response packet is sent by the server in response to
    an SMB2 SESSION_SETUP Request.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=9,
            )),
            ('session_flags', FlagField(
                size=2,
                flag_type=SessionFlags,
            )),
            ('security_buffer_offset', IntField(
                size=2,
                default=72,  # (header size 64) + (response size 8)
            )),
            ('security_buffer_length', IntField(
                size=2,
                default=lambda s: len(s['buffer']),
            )),
            ('buffer', BytesField(
                size=lambda s: s['security_buffer_length'].get_value(),
            ))
        ])
        super(SMB2SessionSetupResponse, self).__init__()


class SMB2Logoff(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.7/8 SMB2 LOGOFF Request/Response
    Request and response to request the termination of a particular session as
    specified by the header.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=4
            )),
            ('reserved', IntField(size=2))
        ])
        super(SMB2Logoff, self).__init__()


class SMB2TreeConnectRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.9 SMB2 TREE_CONNECT Request
    Sent by the client to request access to a particular share on the server
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=9
            )),
            ('flags', FlagField(
                size=2,
                flag_type=TreeFlags,
            )),
            ('path_offset', IntField(
                size=2,
                default=64 + 8,
            )),
            ('path_length', IntField(
                size=2,
                default=lambda s: len(s['buffer']),
            )),
            ('buffer', BytesField())
        ])
        super(SMB2TreeConnectRequest, self).__init__()


class SMB2TreeConnectResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.10 SMB2 TREE_CONNECT Response
    Sent by the server when an SMB2 TREE_CONNECT request is processed
    successfully.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=16
            )),
            ('share_type', EnumField(
                size=1,
                enum_type=ShareType,
            )),
            ('reserved', IntField(size=1)),
            ('share_flags', FlagField(
                size=4,
                flag_type=ShareFlags,
            )),
            ('capabilities', FlagField(
                size=4,
                flag_type=ShareCapabilities,
            )),
            ('maximal_access', IntField(size=4))
        ])
        super(SMB2TreeConnectResponse, self).__init__()


class SMB2TreeDisconnect(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.11/12 SMB2 TREE_DISCONNECT Request and Response
    Sent by the client to request that the tree connect specific by tree_id in
    the header is disconnected.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=4,
            )),
            ('reserved', IntField(size=2))
        ])
        super(SMB2TreeDisconnect, self).__init__()


class SMB2CreateRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.13 SMB2 CREATE Request
    The SMB2 Create Request packet is sent by a client to request either
    creation of or access to a file.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=57,
            )),
            ('security_flags', IntField(size=1)),
            ('requested_oplock_level', EnumField(
                size=1,
                enum_type=RequestedOplockLevel
            )),
            ('impersonation_level', EnumField(
                size=4,
                enum_type=ImpersonationLevel
            )),
            ('smb_create_flags', IntField(size=8)),
            ('reserved', IntField(size=8)),
            ('desired_access', IntField(size=4)),
            ('file_attributes', IntField(size=4)),
            ('share_access', FlagField(
                size=4,
                flag_type=ShareAccess
            )),
            ('create_disposition', EnumField(
                size=4,
                enum_type=CreateDisposition
            )),
            ('create_options', FlagField(
                size=4,
                flag_type=CreateOptions
            )),
            ('name_offset', IntField(
                size=2,
                default=120  # (header size 64) + (structure size 56)
            )),
            ('name_length', IntField(
                size=2,
                default=lambda s: len(s['buffer_path'])
            )),
            ('create_contexts_offset', IntField(
                size=4,
                default=lambda s: self._create_contexts_offset(s)
            )),
            ('create_contexts_length', IntField(
                size=4,
                default=lambda s: len(s['buffer_context'])
            )),
            # Technically these are all under buffer but we split it to make
            # things easier
            ('buffer_path', BytesField(
                size=lambda s: s['name_length'].get_value(),
            )),
            ('padding', BytesField(
                size=lambda s: self._padding_size(s),
                default=lambda s: b"\x00" * self._padding_size(s)
            )),
            ('buffer_context', ListField(
                size=lambda s: s['create_contexts_length'].get_value(),
                unpack_func=lambda s, d: self._buffer_context_list(s, d)
            ))
        ])
        super(SMB2CreateRequest, self).__init__()

    def _create_contexts_offset(self, structure):
        if len(structure['buffer_context']) == 0:
            return 0
        else:
            return structure['name_offset'].get_value() + \
                   structure['padding'].get_value()

    def _padding_size(self, structure):
        # no padding is needed if there are no contexts
        if len(structure['buffer_context']) == 0:
            return 0

        mod = structure['name_length'].get_value() % 8
        return 0 if mod == 0 else 8 - mod

    def _buffer_context_list(self, structure, data):
        context_list = []
        last_context = False
        while not last_context:
            field, data = self._parse_create_context_entry(data)
            last_context = field['next'].get_value() == 0

        return context_list

    def _parse_create_context_entry(self, data):
        create_context = SMB2CreateContextRequest()
        create_context.unpack(data)
        return create_context, data[len(create_context):]


class SMB2CreateContextRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.13.2 SMB2_CREATE_CONTEXT Request Values
    Structure used in the SMB2 CREATE Request and SMB2 CREATE Response to
    encode additional flags and attributes
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('next', IntField(size=4)),
            ('name_offset', IntField(
                size=2,
                default=16
            )),
            ('name_length', IntField(
                size=2,
                default=lambda s: len(s['buffer_name'])
            )),
            ('reserved', IntField(size=2)),
            ('data_offset', IntField(
                size=2,
                default=lambda s: self._buffer_data_offset(s)
            )),
            ('data_length', IntField(
                size=4,
                default=lambda s: len(s['buffer_data'])
            )),
            ('buffer_name', EnumField(
                size=lambda s: s['name_length'].get_value(),
                enum_type=CreateContextName
            )),
            ('padding', BytesField(
                size=lambda s: self._padding_size(s),
                default=lambda s: b"\x00" * self._padding_size(s)
            )),
            ('buffer_data', BytesField(
                size=lambda s: s['data_length'].get_value()
            ))
        ])
        super(SMB2CreateContextRequest, self).__init__()

    def _buffer_data_offset(self, structure):
        if structure['data_length'].get_value() == 0:
            return 0
        else:
            return structure['name_offset'].get_value() + \
                   len(structure['padding'])

    def _padding_size(self, structure):
        if structure['data_length'].get_value() == 0:
            return 0

        mod = structure['data_length'].get_value() % 8
        return 0 if mod == 0 else 8 - mod


class SMB2CreateResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.14 SMB2 CREATE Response
    The SMB2 Create Response packet is sent by the server to an SMB2 CREATE
    Request.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=89
            )),
            ('oplock_level', EnumField(
                size=1,
                enum_type=RequestedOplockLevel
            )),
            ('flag', FlagField(
                size=1,
                flag_type=FileFlags
            )),
            ('create_action', EnumField(
                size=4,
                enum_type=CreateAction
            )),
            ('creation_time', DateTimeField()),
            ('last_access_time', DateTimeField()),
            ('last_write_time', DateTimeField()),
            ('change_time', DateTimeField()),
            ('allocation_size', IntField(size=8)),
            ('end_of_file', IntField(size=8)),
            ('file_attributes', FlagField(
                size=4,
                flag_type=FileAttributes
            )),
            ('reserved2', IntField(size=4)),
            ('file_id', StructureField(
                size=16,
                structure_type=SMB2FileId
            )),
            ('create_contexts_offset', IntField(size=4)),
            ('create_contexts_length', IntField(size=4)),
            ('buffer', BytesField())
        ])
        super(SMB2CreateResponse, self).__init__()


class SMB2FileId(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.14.1 SMB2_FILEID
    Used to represent an open to a file
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('persistent', BytesField(size=8)),
            ('volatile', BytesField(size=8)),
        ])
        super(SMB2FileId, self).__init__()


class SMB2CloseRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.15 SMB2 CLOSE Request
    Used by the client to close an instance of a file
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=24
            )),
            ('flags', FlagField(
                size=2,
                flag_type=CloseFlags
            )),
            ('reserved', IntField(size=4)),
            ('file_id', StructureField(
                size=16,
                structure_type=SMB2FileId
            ))
        ])
        super(SMB2CloseRequest, self).__init__()


class SMB2CloseResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.16 SMB2 CLOSE Response
    The response of a SMB2 CLOSE Request
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(
                size=2,
                default=60
            )),
            ('flags', FlagField(
                size=2,
                flag_type=CloseFlags
            )),
            ('reserved', IntField(size=4)),
            ('creation_time', DateTimeField()),
            ('last_access_time', DateTimeField()),
            ('last_write_time', DateTimeField()),
            ('change_time', DateTimeField()),
            ('allocation_size', IntField(size=8)),
            ('end_of_file', IntField(size=8)),
            ('file_attributes', FlagField(
                size=4,
                flag_type=FileAttributes
            ))
        ])
        super(SMB2CloseResponse, self).__init__()


class SMB2IOCTLRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.31 SMB2 IOCTL Request
    Send by the client to issue an implementation-specific file system control
    or device control command across the network.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(size=2, default=57)),
            ('reserved', IntField(size=2, default=0)),
            ('ctl_code', EnumField(
                size=4,
                enum_type=CtlCode,
            )),
            ('file_id', StructureField(
                size=16,
                structure_type=SMB2FileId
            )),
            ('input_offset', IntField(
                size=4,
                default=lambda s: self._buffer_offset_value(s)
            )),
            ('input_count', IntField(
                size=4,
                default=lambda s: len(s['buffer']),
            )),
            ('max_input_response', IntField(size=4)),
            ('output_offset', IntField(
                size=4,
                default=lambda s: self._buffer_offset_value(s)
            )),
            ('output_count', IntField(size=4, default=0)),
            ('max_output_response', IntField(size=4)),
            ('flags', EnumField(
                size=4,
                enum_type=IOCTLFlags,
            )),
            ('reserved2', IntField(size=4, default=0)),
            ('buffer', BytesField(
                size=lambda s: s['input_count'].get_value()
            ))
        ])
        super(SMB2IOCTLRequest, self).__init__()

    def _buffer_offset_value(self, structure):
        # The offset from the beginning of the SMB2 header to the value of the
        # buffer, 0 if no buffer is set
        if len(structure['buffer']) > 0:
            header_size = 64
            request_size = structure['structure_size'].get_value()
            return header_size + request_size - 1
        else:
            return 0


class SMB2ValidateNegotiateInfoRequest(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.31.4 VALIDATE_NEGOTIATE_INFO Request
    Packet sent to the server to request validation of a previous SMB 2
    NEGOTIATE request.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('capabilities', FlagField(
                size=4,
                flag_type=Capabilities,
            )),
            ('guid', UuidField()),
            ('security_mode', EnumField(
                size=2,
                enum_type=SecurityMode,
            )),
            ('dialect_count', IntField(
                size=2,
                default=lambda s: len(s['dialects'].get_value())
            )),
            ('dialects', ListField(
                size=lambda s: s['dialect_count'].get_value() * 2,
                list_count=lambda s: s['dialect_count'].get_value(),
                list_type=EnumField(size=2, enum_type=Dialects),
            ))
        ])
        super(SMB2ValidateNegotiateInfoRequest, self).__init__()


class SMB2IOCTLResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.32 SMB2 IOCTL Response
    Sent by the server to transmit the results of a client SMB2 IOCTL Request.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('structure_size', IntField(size=2, default=49)),
            ('reserved', IntField(size=2, default=0)),
            ('ctl_code', EnumField(
                size=4,
                enum_type=CtlCode,
            )),
            ('file_id', StructureField(
                size=16,
                structure_type=SMB2FileId
            )),
            ('input_offset', IntField(size=4)),
            ('input_count', IntField(size=4)),
            ('output_offset', IntField(size=4)),
            ('output_count', IntField(size=4)),
            ('flags', IntField(size=4, default=0)),
            ('reserved2', IntField(size=4, default=0)),
            ('buffer', BytesField(
                size=lambda s: s['output_count'].get_value(),
            ))
        ])
        super(SMB2IOCTLResponse, self).__init__()


class SMB2ValidateNegotiateInfoResponse(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.32.6 VALIDATE_NEGOTIATE_INFO Response
    Packet sent by the server on a request validation of SMB 2 negotiate
    request.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('capabilities', FlagField(
                size=4,
                flag_type=Capabilities,
            )),
            ('guid', UuidField()),
            ('security_mode', EnumField(
                size=2,
                enum_type=SecurityMode,
            )),
            ('dialect', EnumField(
                size=2,
                enum_type=Dialects
            ))
        ])
        super(SMB2ValidateNegotiateInfoResponse, self).__init__()


class SMB2TransformHeader(Structure):
    """
    [MS-SMB2] v53.0 2017-09-15

    2.2.41 SMB@ TRANSFORM_HEADER
    The SMB2 Transform Header is used by the client or server when sending
    encrypted message. This is only valid for the SMB.x dialect family.
    """

    def __init__(self):
        self.fields = OrderedDict([
            ('protocol_id', BytesField(
                size=4,
                default=b"\xfdSMB"
            )),
            ('signature', BytesField(
                size=16,
                default=b"\x00" * 16
            )),
            ('nonce', BytesField(size=16)),
            ('original_message_size', IntField(size=4)),
            ('reserved', IntField(size=2, default=0)),
            ('flags', IntField(
                size=2,
                default=1
            )),
            ('session_id', IntField(size=8)),
            ('data', BytesField())  # not in spec
        ])
        super(SMB2TransformHeader, self).__init__()
