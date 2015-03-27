# -*- coding: utf-8 -*-

import struct
import wad

class DoomTexturesError(Exception):
	pass

class DoomPatch:
	def __init__(self):
		self.xorg = 0
		self.yorg = 0
		self.name = ''

class DoomTexture:
	def __init__(self):
		self.name = ''
		self.flags = 0
		self.xscale = 1
		self.yscale = 1
		self.width = 0
		self.height = 0
		self.patches = []

class DoomTextures:
	def __init__(self):
		self.textures = []

	def read(self, wf, name): # TEXTURE1, TEXTURE2, TEXTURES. in case of TEXTURE#, additional PNAMES lump will be read
		if name == 'TEXTURES':
			raise DoomTexturesError('TEXTURES not supported yet')
		lmp_tx = wf.get_num_for_name(name)
		if lmp_tx < 0:
			raise DoomTexturesError('TEXTURE# lump not found')
		pnames = []
		lmp_pnames = wf.get_num_for_name('PNAMES')
		if lmp_pnames < 0:
			raise DoomTexturesError('PNAMES lump not found')
		# read pnames
		ent_pnames = wf.entries[lmp_pnames]
		pn_count = struct.unpack('<I', ent_pnames.data[0:4])[0]
		for i in range(pn_count):
			pnames.append(wad.null_term_string(ent_pnames.data[4+i*8:4+i*8+8]))
		ent_tx = wf.entries[lmp_tx]
		tx_cnt = struct.unpack('<I', ent_tx.data[0:4])[0]
		tx_offs = []
		for i in range(tx_cnt):
			tx_offs.append(struct.unpack('<I', ent_tx.data[4+i*4:4+i*4+4])[0])
		is_strife = False
		for offs in tx_offs:
			tx = DoomTexture()
			tx.name = wad.null_term_string(ent_tx.data[offs:offs+8]).upper()
			tx.flags = struct.unpack('<H', ent_tx.data[offs+8:offs+8+2])[0]
			tx.xscale, tx.yscale = struct.unpack('<BB', ent_tx.data[offs+8+2:offs+8+4])
			tx.width, tx.height = struct.unpack('<HH', ent_tx.data[offs+8+4:offs+8+8])
			cd1, cd2 = struct.unpack('<HH', ent_tx.data[offs+8+8:offs+8+8+4])
			if cd2 != 0 or is_strife:
				patchcount = cd1
				is_strife = True
			else:
				patchcount = struct.unpack('<H', ent_tx.data[offs+8+12:offs+8+12+2])[0]
			psz = 10 if not is_strife else 6 #size of one patch struct
			for i in range(patchcount):
				patch = DoomPatch()#22
				patch.xorg, patch.yorg = struct.unpack('<hh', ent_tx.data[offs+22+i*psz:offs+22+i*psz+4])
				patch.name = pnames[struct.unpack('<H', ent_tx.data[offs+22+i*psz+4:offs+22+i*psz+6])[0]].upper()
				tx.patches.append(patch)
			self.textures.append(tx)

	def write(self, wf, name): # TEXTURE1, TEXTURE2, TEXTURES. in case of TEXTURE#, additional PNAMES lump will be written
		if name == 'TEXTURES':
			raise DoomTexturesError('TEXTURES not supported yet')
		# check for existing texture# and pnames
		lmp_tx = wf.get_num_for_name(name)
		if lmp_tx < 0:
			lmp_tx = len(wf.entries)
			wf.entries.append(wad.WADEntry(name, bytes(), 0))
		lmp_pnames = wf.get_num_for_name('PNAMES')
		if lmp_pnames < 0:
			lmp_pnames = len(wf.entries)
			wf.entries.append(wad.WADEntry('PNAMES', bytes(), 0))
		pnames = []
		texdata = bytes()
		texdata += struct.pack('<I', len(self.textures))
		offscalc = 4+len(self.textures)*4
		for i in range(len(self.textures)):
			texdata += struct.pack('<I', offscalc)
			offscalc += 22+len(self.textures[i].patches)*10
		for tx in self.textures:
			texdata0 = struct.pack('<8sHBBHHIH', tx.name.encode('ascii'), tx.flags, tx.xscale, tx.yscale, tx.width, tx.height, 0, len(tx.patches))
			for patch in tx.patches:
				try:
					idx = pnames.index(patch.name)
				except ValueError:
					idx = len(pnames)
					pnames.append(patch.name)
				texdata0 += struct.pack('<hhHHH', patch.xorg, patch.yorg, idx, 0, 0)
			texdata += texdata0
		wf.entries[lmp_tx].data = texdata
		pnamedata = bytes()
		pnamedata += struct.pack('<I', len(pnames))
		for pname in pnames:
			pnamedata += struct.pack('<8s', pname.encode('ascii'))
		wf.entries[lmp_pnames].data = pnamedata
