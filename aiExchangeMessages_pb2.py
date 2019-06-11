# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: code/drivebuild/schemes/aiExchangeMessages.proto

import sys
_b=sys.version_info[0]<3 and (lambda x:x) or (lambda x:x.encode('latin1'))
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor.FileDescriptor(
  name='code/drivebuild/schemes/aiExchangeMessages.proto',
  package='',
  syntax='proto3',
  serialized_options=_b('\220\001\000'),
  serialized_pb=_b('\n0code/drivebuild/schemes/aiExchangeMessages.proto\";\n\x0b\x44\x61taRequest\x12\x17\n\x03vid\x18\x01 \x01(\x0b\x32\n.VehicleID\x12\x13\n\x0brequest_ids\x18\x02 \x03(\t\"\xe7\x04\n\x0c\x44\x61taResponse\x12%\n\x04\x64\x61ta\x18\x01 \x03(\x0b\x32\x17.DataResponse.DataEntry\x1a\xee\x03\n\x04\x44\x61ta\x12/\n\x08position\x18\x01 \x01(\x0b\x32\x1b.DataResponse.Data.PositionH\x00\x12)\n\x05speed\x18\x02 \x01(\x0b\x32\x18.DataResponse.Data.SpeedH\x00\x12\x31\n\x05\x61ngle\x18\x03 \x01(\x0b\x32 .DataResponse.Data.SteeringAngleH\x00\x12)\n\x05lidar\x18\x04 \x01(\x0b\x32\x18.DataResponse.Data.LidarH\x00\x12+\n\x06\x63\x61mera\x18\x05 \x01(\x0b\x32\x19.DataResponse.Data.CameraH\x00\x12+\n\x06\x64\x61mage\x18\x06 \x01(\x0b\x32\x19.DataResponse.Data.DamageH\x00\x1a \n\x08Position\x12\t\n\x01x\x18\x01 \x01(\x01\x12\t\n\x01y\x18\x02 \x01(\x01\x1a\x16\n\x05Speed\x12\r\n\x05speed\x18\x01 \x01(\x01\x1a\x1e\n\rSteeringAngle\x12\r\n\x05\x61ngle\x18\x01 \x01(\x01\x1a\x17\n\x05Lidar\x12\x0e\n\x06points\x18\x01 \x03(\x01\x1a\x39\n\x06\x43\x61mera\x12\r\n\x05\x63olor\x18\x01 \x01(\x0c\x12\x11\n\tannotated\x18\x02 \x01(\x0c\x12\r\n\x05\x64\x65pth\x18\x03 \x01(\x0c\x1a\x1c\n\x06\x44\x61mage\x12\x12\n\nis_damaged\x18\x01 \x01(\x08\x42\x06\n\x04\x64\x61ta\x1a?\n\tDataEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12!\n\x05value\x18\x02 \x01(\x0b\x32\x12.DataResponse.Data:\x02\x38\x01\"\xf0\x01\n\x07\x43ontrol\x12\x17\n\x03vid\x18\x01 \x01(\x0b\x32\n.VehicleID\x12\'\n\tavCommand\x18\x02 \x01(\x0b\x32\x12.Control.AvCommandH\x00\x12)\n\nsimCommand\x18\x03 \x01(\x0e\x32\x13.Control.SimCommandH\x00\x1a=\n\tAvCommand\x12\x12\n\naccelerate\x18\x01 \x01(\x01\x12\r\n\x05steer\x18\x02 \x01(\x01\x12\r\n\x05\x62rake\x18\x03 \x01(\x01\".\n\nSimCommand\x12\n\n\x06RESUME\x10\x00\x12\x08\n\x04\x46\x41IL\x10\x01\x12\n\n\x06\x43\x41NCEL\x10\x02\x42\t\n\x07\x63ommand\"\x18\n\tVehicleID\x12\x0b\n\x03vid\x18\x01 \x01(\t\"\x7f\n\x10SimStateResponse\x12)\n\x05state\x18\x01 \x01(\x0e\x32\x1a.SimStateResponse.SimState\"@\n\x08SimState\x12\x0b\n\x07RUNNING\x10\x00\x12\x0c\n\x08\x46INISHED\x10\x01\x12\x0c\n\x08\x43\x41NCELED\x10\x02\x12\x0b\n\x07\x45RRORED\x10\x03\"\x06\n\x04Void2\x99\x01\n\x11\x41IExchangeService\x12;\n\x1await_for_simulator_request\x12\n.VehicleID\x1a\x11.SimStateResponse\x12+\n\x0crequest_data\x12\x0c.DataRequest\x1a\r.DataResponse\x12\x1a\n\x07\x63ontrol\x12\x08.Control\x1a\x05.VoidB\x03\x90\x01\x00\x62\x06proto3')
)



_CONTROL_SIMCOMMAND = _descriptor.EnumDescriptor(
  name='SimCommand',
  full_name='Control.SimCommand',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='RESUME', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='FAIL', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CANCEL', index=2, number=2,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=915,
  serialized_end=961,
)
_sym_db.RegisterEnumDescriptor(_CONTROL_SIMCOMMAND)

_SIMSTATERESPONSE_SIMSTATE = _descriptor.EnumDescriptor(
  name='SimState',
  full_name='SimStateResponse.SimState',
  filename=None,
  file=DESCRIPTOR,
  values=[
    _descriptor.EnumValueDescriptor(
      name='RUNNING', index=0, number=0,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='FINISHED', index=1, number=1,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='CANCELED', index=2, number=2,
      serialized_options=None,
      type=None),
    _descriptor.EnumValueDescriptor(
      name='ERRORED', index=3, number=3,
      serialized_options=None,
      type=None),
  ],
  containing_type=None,
  serialized_options=None,
  serialized_start=1063,
  serialized_end=1127,
)
_sym_db.RegisterEnumDescriptor(_SIMSTATERESPONSE_SIMSTATE)


_DATAREQUEST = _descriptor.Descriptor(
  name='DataRequest',
  full_name='DataRequest',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='vid', full_name='DataRequest.vid', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='request_ids', full_name='DataRequest.request_ids', index=1,
      number=2, type=9, cpp_type=9, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=52,
  serialized_end=111,
)


_DATARESPONSE_DATA_POSITION = _descriptor.Descriptor(
  name='Position',
  full_name='DataResponse.Data.Position',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='x', full_name='DataResponse.Data.Position.x', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='y', full_name='DataResponse.Data.Position.y', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=454,
  serialized_end=486,
)

_DATARESPONSE_DATA_SPEED = _descriptor.Descriptor(
  name='Speed',
  full_name='DataResponse.Data.Speed',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='speed', full_name='DataResponse.Data.Speed.speed', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=488,
  serialized_end=510,
)

_DATARESPONSE_DATA_STEERINGANGLE = _descriptor.Descriptor(
  name='SteeringAngle',
  full_name='DataResponse.Data.SteeringAngle',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='angle', full_name='DataResponse.Data.SteeringAngle.angle', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=512,
  serialized_end=542,
)

_DATARESPONSE_DATA_LIDAR = _descriptor.Descriptor(
  name='Lidar',
  full_name='DataResponse.Data.Lidar',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='points', full_name='DataResponse.Data.Lidar.points', index=0,
      number=1, type=1, cpp_type=5, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=544,
  serialized_end=567,
)

_DATARESPONSE_DATA_CAMERA = _descriptor.Descriptor(
  name='Camera',
  full_name='DataResponse.Data.Camera',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='color', full_name='DataResponse.Data.Camera.color', index=0,
      number=1, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='annotated', full_name='DataResponse.Data.Camera.annotated', index=1,
      number=2, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='depth', full_name='DataResponse.Data.Camera.depth', index=2,
      number=3, type=12, cpp_type=9, label=1,
      has_default_value=False, default_value=_b(""),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=569,
  serialized_end=626,
)

_DATARESPONSE_DATA_DAMAGE = _descriptor.Descriptor(
  name='Damage',
  full_name='DataResponse.Data.Damage',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='is_damaged', full_name='DataResponse.Data.Damage.is_damaged', index=0,
      number=1, type=8, cpp_type=7, label=1,
      has_default_value=False, default_value=False,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=628,
  serialized_end=656,
)

_DATARESPONSE_DATA = _descriptor.Descriptor(
  name='Data',
  full_name='DataResponse.Data',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='position', full_name='DataResponse.Data.position', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='speed', full_name='DataResponse.Data.speed', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='angle', full_name='DataResponse.Data.angle', index=2,
      number=3, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='lidar', full_name='DataResponse.Data.lidar', index=3,
      number=4, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='camera', full_name='DataResponse.Data.camera', index=4,
      number=5, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='damage', full_name='DataResponse.Data.damage', index=5,
      number=6, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_DATARESPONSE_DATA_POSITION, _DATARESPONSE_DATA_SPEED, _DATARESPONSE_DATA_STEERINGANGLE, _DATARESPONSE_DATA_LIDAR, _DATARESPONSE_DATA_CAMERA, _DATARESPONSE_DATA_DAMAGE, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='data', full_name='DataResponse.Data.data',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=170,
  serialized_end=664,
)

_DATARESPONSE_DATAENTRY = _descriptor.Descriptor(
  name='DataEntry',
  full_name='DataResponse.DataEntry',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='key', full_name='DataResponse.DataEntry.key', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='value', full_name='DataResponse.DataEntry.value', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=_b('8\001'),
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=666,
  serialized_end=729,
)

_DATARESPONSE = _descriptor.Descriptor(
  name='DataResponse',
  full_name='DataResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='data', full_name='DataResponse.data', index=0,
      number=1, type=11, cpp_type=10, label=3,
      has_default_value=False, default_value=[],
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_DATARESPONSE_DATA, _DATARESPONSE_DATAENTRY, ],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=114,
  serialized_end=729,
)


_CONTROL_AVCOMMAND = _descriptor.Descriptor(
  name='AvCommand',
  full_name='Control.AvCommand',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='accelerate', full_name='Control.AvCommand.accelerate', index=0,
      number=1, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='steer', full_name='Control.AvCommand.steer', index=1,
      number=2, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='brake', full_name='Control.AvCommand.brake', index=2,
      number=3, type=1, cpp_type=5, label=1,
      has_default_value=False, default_value=float(0),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=852,
  serialized_end=913,
)

_CONTROL = _descriptor.Descriptor(
  name='Control',
  full_name='Control',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='vid', full_name='Control.vid', index=0,
      number=1, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='avCommand', full_name='Control.avCommand', index=1,
      number=2, type=11, cpp_type=10, label=1,
      has_default_value=False, default_value=None,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
    _descriptor.FieldDescriptor(
      name='simCommand', full_name='Control.simCommand', index=2,
      number=3, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[_CONTROL_AVCOMMAND, ],
  enum_types=[
    _CONTROL_SIMCOMMAND,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
    _descriptor.OneofDescriptor(
      name='command', full_name='Control.command',
      index=0, containing_type=None, fields=[]),
  ],
  serialized_start=732,
  serialized_end=972,
)


_VEHICLEID = _descriptor.Descriptor(
  name='VehicleID',
  full_name='VehicleID',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='vid', full_name='VehicleID.vid', index=0,
      number=1, type=9, cpp_type=9, label=1,
      has_default_value=False, default_value=_b("").decode('utf-8'),
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=974,
  serialized_end=998,
)


_SIMSTATERESPONSE = _descriptor.Descriptor(
  name='SimStateResponse',
  full_name='SimStateResponse',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
    _descriptor.FieldDescriptor(
      name='state', full_name='SimStateResponse.state', index=0,
      number=1, type=14, cpp_type=8, label=1,
      has_default_value=False, default_value=0,
      message_type=None, enum_type=None, containing_type=None,
      is_extension=False, extension_scope=None,
      serialized_options=None, file=DESCRIPTOR),
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
    _SIMSTATERESPONSE_SIMSTATE,
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1000,
  serialized_end=1127,
)


_VOID = _descriptor.Descriptor(
  name='Void',
  full_name='Void',
  filename=None,
  file=DESCRIPTOR,
  containing_type=None,
  fields=[
  ],
  extensions=[
  ],
  nested_types=[],
  enum_types=[
  ],
  serialized_options=None,
  is_extendable=False,
  syntax='proto3',
  extension_ranges=[],
  oneofs=[
  ],
  serialized_start=1129,
  serialized_end=1135,
)

_DATAREQUEST.fields_by_name['vid'].message_type = _VEHICLEID
_DATARESPONSE_DATA_POSITION.containing_type = _DATARESPONSE_DATA
_DATARESPONSE_DATA_SPEED.containing_type = _DATARESPONSE_DATA
_DATARESPONSE_DATA_STEERINGANGLE.containing_type = _DATARESPONSE_DATA
_DATARESPONSE_DATA_LIDAR.containing_type = _DATARESPONSE_DATA
_DATARESPONSE_DATA_CAMERA.containing_type = _DATARESPONSE_DATA
_DATARESPONSE_DATA_DAMAGE.containing_type = _DATARESPONSE_DATA
_DATARESPONSE_DATA.fields_by_name['position'].message_type = _DATARESPONSE_DATA_POSITION
_DATARESPONSE_DATA.fields_by_name['speed'].message_type = _DATARESPONSE_DATA_SPEED
_DATARESPONSE_DATA.fields_by_name['angle'].message_type = _DATARESPONSE_DATA_STEERINGANGLE
_DATARESPONSE_DATA.fields_by_name['lidar'].message_type = _DATARESPONSE_DATA_LIDAR
_DATARESPONSE_DATA.fields_by_name['camera'].message_type = _DATARESPONSE_DATA_CAMERA
_DATARESPONSE_DATA.fields_by_name['damage'].message_type = _DATARESPONSE_DATA_DAMAGE
_DATARESPONSE_DATA.containing_type = _DATARESPONSE
_DATARESPONSE_DATA.oneofs_by_name['data'].fields.append(
  _DATARESPONSE_DATA.fields_by_name['position'])
_DATARESPONSE_DATA.fields_by_name['position'].containing_oneof = _DATARESPONSE_DATA.oneofs_by_name['data']
_DATARESPONSE_DATA.oneofs_by_name['data'].fields.append(
  _DATARESPONSE_DATA.fields_by_name['speed'])
_DATARESPONSE_DATA.fields_by_name['speed'].containing_oneof = _DATARESPONSE_DATA.oneofs_by_name['data']
_DATARESPONSE_DATA.oneofs_by_name['data'].fields.append(
  _DATARESPONSE_DATA.fields_by_name['angle'])
_DATARESPONSE_DATA.fields_by_name['angle'].containing_oneof = _DATARESPONSE_DATA.oneofs_by_name['data']
_DATARESPONSE_DATA.oneofs_by_name['data'].fields.append(
  _DATARESPONSE_DATA.fields_by_name['lidar'])
_DATARESPONSE_DATA.fields_by_name['lidar'].containing_oneof = _DATARESPONSE_DATA.oneofs_by_name['data']
_DATARESPONSE_DATA.oneofs_by_name['data'].fields.append(
  _DATARESPONSE_DATA.fields_by_name['camera'])
_DATARESPONSE_DATA.fields_by_name['camera'].containing_oneof = _DATARESPONSE_DATA.oneofs_by_name['data']
_DATARESPONSE_DATA.oneofs_by_name['data'].fields.append(
  _DATARESPONSE_DATA.fields_by_name['damage'])
_DATARESPONSE_DATA.fields_by_name['damage'].containing_oneof = _DATARESPONSE_DATA.oneofs_by_name['data']
_DATARESPONSE_DATAENTRY.fields_by_name['value'].message_type = _DATARESPONSE_DATA
_DATARESPONSE_DATAENTRY.containing_type = _DATARESPONSE
_DATARESPONSE.fields_by_name['data'].message_type = _DATARESPONSE_DATAENTRY
_CONTROL_AVCOMMAND.containing_type = _CONTROL
_CONTROL.fields_by_name['vid'].message_type = _VEHICLEID
_CONTROL.fields_by_name['avCommand'].message_type = _CONTROL_AVCOMMAND
_CONTROL.fields_by_name['simCommand'].enum_type = _CONTROL_SIMCOMMAND
_CONTROL_SIMCOMMAND.containing_type = _CONTROL
_CONTROL.oneofs_by_name['command'].fields.append(
  _CONTROL.fields_by_name['avCommand'])
_CONTROL.fields_by_name['avCommand'].containing_oneof = _CONTROL.oneofs_by_name['command']
_CONTROL.oneofs_by_name['command'].fields.append(
  _CONTROL.fields_by_name['simCommand'])
_CONTROL.fields_by_name['simCommand'].containing_oneof = _CONTROL.oneofs_by_name['command']
_SIMSTATERESPONSE.fields_by_name['state'].enum_type = _SIMSTATERESPONSE_SIMSTATE
_SIMSTATERESPONSE_SIMSTATE.containing_type = _SIMSTATERESPONSE
DESCRIPTOR.message_types_by_name['DataRequest'] = _DATAREQUEST
DESCRIPTOR.message_types_by_name['DataResponse'] = _DATARESPONSE
DESCRIPTOR.message_types_by_name['Control'] = _CONTROL
DESCRIPTOR.message_types_by_name['VehicleID'] = _VEHICLEID
DESCRIPTOR.message_types_by_name['SimStateResponse'] = _SIMSTATERESPONSE
DESCRIPTOR.message_types_by_name['Void'] = _VOID
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

DataRequest = _reflection.GeneratedProtocolMessageType('DataRequest', (_message.Message,), dict(
  DESCRIPTOR = _DATAREQUEST,
  __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
  # @@protoc_insertion_point(class_scope:DataRequest)
  ))
_sym_db.RegisterMessage(DataRequest)

DataResponse = _reflection.GeneratedProtocolMessageType('DataResponse', (_message.Message,), dict(

  Data = _reflection.GeneratedProtocolMessageType('Data', (_message.Message,), dict(

    Position = _reflection.GeneratedProtocolMessageType('Position', (_message.Message,), dict(
      DESCRIPTOR = _DATARESPONSE_DATA_POSITION,
      __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
      # @@protoc_insertion_point(class_scope:DataResponse.Data.Position)
      ))
    ,

    Speed = _reflection.GeneratedProtocolMessageType('Speed', (_message.Message,), dict(
      DESCRIPTOR = _DATARESPONSE_DATA_SPEED,
      __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
      # @@protoc_insertion_point(class_scope:DataResponse.Data.Speed)
      ))
    ,

    SteeringAngle = _reflection.GeneratedProtocolMessageType('SteeringAngle', (_message.Message,), dict(
      DESCRIPTOR = _DATARESPONSE_DATA_STEERINGANGLE,
      __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
      # @@protoc_insertion_point(class_scope:DataResponse.Data.SteeringAngle)
      ))
    ,

    Lidar = _reflection.GeneratedProtocolMessageType('Lidar', (_message.Message,), dict(
      DESCRIPTOR = _DATARESPONSE_DATA_LIDAR,
      __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
      # @@protoc_insertion_point(class_scope:DataResponse.Data.Lidar)
      ))
    ,

    Camera = _reflection.GeneratedProtocolMessageType('Camera', (_message.Message,), dict(
      DESCRIPTOR = _DATARESPONSE_DATA_CAMERA,
      __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
      # @@protoc_insertion_point(class_scope:DataResponse.Data.Camera)
      ))
    ,

    Damage = _reflection.GeneratedProtocolMessageType('Damage', (_message.Message,), dict(
      DESCRIPTOR = _DATARESPONSE_DATA_DAMAGE,
      __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
      # @@protoc_insertion_point(class_scope:DataResponse.Data.Damage)
      ))
    ,
    DESCRIPTOR = _DATARESPONSE_DATA,
    __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
    # @@protoc_insertion_point(class_scope:DataResponse.Data)
    ))
  ,

  DataEntry = _reflection.GeneratedProtocolMessageType('DataEntry', (_message.Message,), dict(
    DESCRIPTOR = _DATARESPONSE_DATAENTRY,
    __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
    # @@protoc_insertion_point(class_scope:DataResponse.DataEntry)
    ))
  ,
  DESCRIPTOR = _DATARESPONSE,
  __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
  # @@protoc_insertion_point(class_scope:DataResponse)
  ))
_sym_db.RegisterMessage(DataResponse)
_sym_db.RegisterMessage(DataResponse.Data)
_sym_db.RegisterMessage(DataResponse.Data.Position)
_sym_db.RegisterMessage(DataResponse.Data.Speed)
_sym_db.RegisterMessage(DataResponse.Data.SteeringAngle)
_sym_db.RegisterMessage(DataResponse.Data.Lidar)
_sym_db.RegisterMessage(DataResponse.Data.Camera)
_sym_db.RegisterMessage(DataResponse.Data.Damage)
_sym_db.RegisterMessage(DataResponse.DataEntry)

Control = _reflection.GeneratedProtocolMessageType('Control', (_message.Message,), dict(

  AvCommand = _reflection.GeneratedProtocolMessageType('AvCommand', (_message.Message,), dict(
    DESCRIPTOR = _CONTROL_AVCOMMAND,
    __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
    # @@protoc_insertion_point(class_scope:Control.AvCommand)
    ))
  ,
  DESCRIPTOR = _CONTROL,
  __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
  # @@protoc_insertion_point(class_scope:Control)
  ))
_sym_db.RegisterMessage(Control)
_sym_db.RegisterMessage(Control.AvCommand)

VehicleID = _reflection.GeneratedProtocolMessageType('VehicleID', (_message.Message,), dict(
  DESCRIPTOR = _VEHICLEID,
  __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
  # @@protoc_insertion_point(class_scope:VehicleID)
  ))
_sym_db.RegisterMessage(VehicleID)

SimStateResponse = _reflection.GeneratedProtocolMessageType('SimStateResponse', (_message.Message,), dict(
  DESCRIPTOR = _SIMSTATERESPONSE,
  __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
  # @@protoc_insertion_point(class_scope:SimStateResponse)
  ))
_sym_db.RegisterMessage(SimStateResponse)

Void = _reflection.GeneratedProtocolMessageType('Void', (_message.Message,), dict(
  DESCRIPTOR = _VOID,
  __module__ = 'code.drivebuild.schemes.aiExchangeMessages_pb2'
  # @@protoc_insertion_point(class_scope:Void)
  ))
_sym_db.RegisterMessage(Void)


DESCRIPTOR._options = None
_DATARESPONSE_DATAENTRY._options = None

_AIEXCHANGESERVICE = _descriptor.ServiceDescriptor(
  name='AIExchangeService',
  full_name='AIExchangeService',
  file=DESCRIPTOR,
  index=0,
  serialized_options=None,
  serialized_start=1138,
  serialized_end=1291,
  methods=[
  _descriptor.MethodDescriptor(
    name='wait_for_simulator_request',
    full_name='AIExchangeService.wait_for_simulator_request',
    index=0,
    containing_service=None,
    input_type=_VEHICLEID,
    output_type=_SIMSTATERESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='request_data',
    full_name='AIExchangeService.request_data',
    index=1,
    containing_service=None,
    input_type=_DATAREQUEST,
    output_type=_DATARESPONSE,
    serialized_options=None,
  ),
  _descriptor.MethodDescriptor(
    name='control',
    full_name='AIExchangeService.control',
    index=2,
    containing_service=None,
    input_type=_CONTROL,
    output_type=_VOID,
    serialized_options=None,
  ),
])
_sym_db.RegisterServiceDescriptor(_AIEXCHANGESERVICE)

DESCRIPTOR.services_by_name['AIExchangeService'] = _AIEXCHANGESERVICE

# @@protoc_insertion_point(module_scope)
