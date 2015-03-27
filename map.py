# -*- coding: utf-8 -*-

import struct
import wad

class DoomMapError(Exception):
	pass

class DoomMapSidedef:
	def __init__(self):
		self.xoffs = 0
		self.yoffs = 0
		self.tex_upper = '-'
		self.tex_lower = '-'
		self.tex_middle = '-'
		self.sector = -1
		self.other = {} # dict used for udmf in the future

class DoomMapSector:
	def __init__(self):
		self.height_floor = 0
		self.height_ceil = 0
		self.tex_floor = '-'
		self.tex_ceil = '-'
		self.light = 192
		self.special = 0
		self.tag = 0

# only SECTORS and SIDEDEFS can be modified right now with this class (only those are required to query/edit texture names)
class DoomMap:
	def __init__(self):
		self.things = []
		self.linedefs = []
		self.sidedefs = []
		self.vertexes = []
		self.sectors = []
		self.scripts = ''
		self.other = {} #wadentries
		self.type = None

	# this function checks for Doom, Hexen or UDMF map. UDMF isn't supported yet.
	def read(self, wf, name):
		def read_lump(entry):
			if entry.name.upper() == 'SIDEDEFS':
				sidecount = int(len(entry.data) / 30)
				for i in range(sidecount):
					_offs = i * 30
					sidedef = DoomMapSidedef()
					sidedef.xoffs, sidedef.yoffs = struct.unpack('<hh', entry.data[_offs:_offs+4])
					sidedef.tex_upper, sidedef.tex_lower, sidedef.tex_middle = struct.unpack('<8s8s8s', entry.data[_offs+4:_offs+4+8*3])
					sidedef.tex_upper = wad.null_term_string(sidedef.tex_upper)
					sidedef.tex_lower = wad.null_term_string(sidedef.tex_lower)
					sidedef.tex_middle = wad.null_term_string(sidedef.tex_middle)
					sidedef.sector = struct.unpack('<h', entry.data[_offs+4+8*3:_offs+4+8*3+2])[0]
					self.sidedefs.append(sidedef)
			elif entry.name.upper() == 'SECTORS':
				sectorcount = int(len(entry.data) / 26)
				for i in range(sectorcount):
					_offs = i * 26
					sector = DoomMapSector()
					sector.height_floor, sector.height_ceil = struct.unpack('<hh', entry.data[_offs:_offs+4])
					sector.tex_floor, sector.tex_ceil = struct.unpack('<8s8s', entry.data[_offs+4:_offs+4+8*2])
					sector.tex_floor = wad.null_term_string(sector.tex_floor)
					sector.tex_ceil = wad.null_term_string(sector.tex_ceil)
					sector.light, sector.special, sector.tag = struct.unpack('<hhh', entry.data[_offs+4+8*2:_offs+4+8*2+6])
					self.sectors.append(sector)
			else:
				self.other[entry.name.upper()] = entry

		self.type = 'Doom'
		# five lumps are required
		# things, linedefs, sidedefs, vertexes, sectors
		# others can be present or not.
		# presence of BEHAVIOR indicates the hexen format.
		# [[<name>, <required>, <num>], ...]
		lumps = [['THINGS', True, -1],
			['LINEDEFS', True, -1],
			['SIDEDEFS', True, -1],
			['VERTEXES', True, -1],
			['SEGS', False, -1],
			['SSECTORS', False, -1],
			['NODES', False, -1],
			['SECTORS', True, -1],
			['REJECT', False, -1],
			['BLOCKMAP', False, -1],
			['BEHAVIOR', False, -1],
			['SCRIPTS', False, -1]]
		ln = wf.get_num_for_name(name)
		if ln < 0:
			raise DoomMapError('Map marker not found')
		ln += 1
		ln_origin = ln
		nolumps = False
		for lump in lumps:
			# check if current lump name matches
			if wf.entries[ln].name.lower() == lump[0].lower():
				lump[2] = ln
				ln += 1
		nolumps = False
		for lump in lumps:
			if lump[1] and lump[2] < 0:
				nolumps = True
				break
			if lump[0].upper() == 'BEHAVIOR' and lump[2] >= 0:
				self.type = 'Hexen'
		if not nolumps:
			for lump in lumps:
				if lump[2] >= 0:
					read_lump(wf.entries[lump[2]])
		else:
			lumps = [['TEXTMAP', True, -1],
				['ZNODES', False, -1],
				['REJECT', False, -1],
				['DIALOGUE', False, -1],
				['BEHAVIOR', False, -1],
				['SCRIPTS', False, -1],
				['ENDMAP', True, -1]]
			ln = ln_origin
			for lump in lumps:
				if wf.entries[ln].name.lower() == lump[0].lower():
					lump[2] = ln
					ln += 1
			nolumps = False
			for lump in lumps:
				if lump[1] and lump[2] < 0:
					nolumps = True
					break
			if not nolumps:
				self.type = 'UDMF'
				for lump in lumps:
					if lump[2] >= 0:
						read_lump(wf.entries[lump[2]])
		if nolumps:
			raise DoomMapError('Required lump(s) not found')
		if self.type == 'UDMF':
			raise DoomMapError('UDMF maps are not supported yet')

	def write(self, wf, name):
		# write lumps in certain order. UDMF maps are not supported.
		if self.type == 'UDMF':
			raise DoomMapError('UDMF maps are not supported yet')
		lumps = [['THINGS', True, -1],
			['LINEDEFS', True, -1],
			['SIDEDEFS', True, -1],
			['VERTEXES', True, -1],
			['SEGS', False, -1],
			['SSECTORS', False, -1],
			['NODES', False, -1],
			['SECTORS', True, -1],
			['REJECT', False, -1],
			['BLOCKMAP', False, -1],
			['BEHAVIOR', False, -1],
			['SCRIPTS', False, -1]]
		wf.entries.append(wad.WADEntry(name, bytes(), 0))
		for lump in lumps:
			if lump[0] == 'BEHAVIOR' or lump[0] == 'SCRIPTS' and self.type != 'Hexen':
				continue
			# put the lump back!
			if lump[0].upper() == 'SIDEDEFS':
				# write sidedefs!
				bd = bytes()
				for sidedef in self.sidedefs:
					bd += struct.pack('<hh8s8s8sh', sidedef.xoffs, sidedef.yoffs, sidedef.tex_upper.encode('ascii'), sidedef.tex_lower.encode('ascii'), sidedef.tex_middle.encode('ascii'), sidedef.sector)
				wf.entries.append(wad.WADEntry('SIDEDEFS', bd, 0))
			elif lump[0].upper() == 'SECTORS':
				# write sectors!
				bd = bytes()
				for sector in self.sectors:
					bd += struct.pack('<hh8s8shhh', sector.height_floor, sector.height_ceil, sector.tex_floor.encode('ascii'), sector.tex_ceil.encode('ascii'), sector.light, sector.special, sector.tag)
				wf.entries.append(wad.WADEntry('SECTORS', bd, 0))
			elif lump[0] in self.other:
				wf.entries.append(self.other[lump[0]])
		if 'BEHAVIOR' not in self.other and self.type == 'Hexen':
			# generate empty behavior
			wf.entries.append(wad.WADEntry('BEHAVIOR', bytes(), 0))
