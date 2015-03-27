# -*- coding: utf-8 -*-

import struct
import zlib

def make_sig(c):
	rt = 0
	for i in reversed(range(len(c))):
		rt |= ord(c[i])
		if i > 0:
			rt <<= 8
	return rt

def null_term_string(s):
	nul = -1
	for i in range(len(s)):
		if s[i] == 0:
			nul = i
			break
	if nul >= 0:
		return s[:nul].decode('ascii')
	return s.decode('ascii')

class WADError(Exception):
	pass

class WADEntry:
	def __init__(self, name, data, offset):
		self.name = name
		self.data = data
		self.offset = offset

	def __repr__(self):
		return 'WADEntry %s[%d]' % (self.name, len(self.data))

	def checksum(self):
		return zlib.adler32(self.data)

class WADFile:
	def __init__(self, filename=None):
		self.type = 'PWAD'
		self.entries = []
		if filename is not None:
			self.read(filename)

	def read(self, filename):
		with open(filename, 'rb') as f:
			WAD_sig, WAD_numlumps, WAD_fatoffs = struct.unpack('<III', f.read(4*3))
			if WAD_sig == make_sig('IWAD'):
				self.type = 'IWAD'
			elif WAD_sig == make_sig('PWAD'):
				self.type = 'PWAD'
			else:
				raise WADError('Invalid signature %08X (expected IWAD or PWAD)' % (WAD_sig))
			for i in range(WAD_numlumps):
				f.seek(WAD_fatoffs+i*16)
				filepos, size, name = struct.unpack('<II8s', f.read(4*2+8))
				#print('%08X %6d %s' % (filepos, size, null_term_string(name)))
				# read in the name and the data
				ent_name = null_term_string(name)
				f.seek(filepos)
				ent_data = f.read(size)
				self.entries.append(WADEntry(ent_name, ent_data, filepos))

	def write(self, filename):
		with open(filename, 'wb') as f:
			f.write(struct.pack('<III', make_sig(self.type), len(self.entries), 0)) # fat offset isn't ready yet... we gotta write the data first
			for i in range(len(self.entries)):
				self.entries[i].offset = f.tell()
				f.write(self.entries[i].data)
			fatoffs = f.tell()
			f.seek(4*2)
			f.write(struct.pack('<I', fatoffs))
			f.seek(fatoffs)
			for entry in self.entries:
				f.write(struct.pack('<II8s', entry.offset, len(entry.data), entry.name.encode('ascii')))

	def get_num_for_name(self, name, pos=None, endpos=None):
		if pos is None:
			pos = 0
		if endpos is None:
			endpos = len(self.entries)
		if pos < 0 or pos >= len(self.entries):
			return -1
		if endpos < pos or endpos < 0 or endpos > len(self.entries):
			return -1
		for i in range(pos, endpos):
			if self.entries[i].name.lower() == name.lower():
				return i
		return -1

	# returns len(self.entries) if theres no next marker
	def get_next_marker(self, pos):
		if pos < 0 or pos >= len(self.entries):
			return len(self.entries)
		for i in range(pos, len(self.entries)):
			if len(self.entries[i].data) == 0:
				return i
		return len(self.entries)
