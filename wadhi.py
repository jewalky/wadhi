# -*- coding: utf-8 -*-

import wad
import map
import tex

import sys
if len(sys.argv) < 4:
	print('Usage: %s <source wad> <map name> <output wad> [output map name]' % (sys.argv[0]))
	exit(0)

CF_Source = sys.argv[1]
CF_SourceMap = sys.argv[2]
CF_Destination = sys.argv[3]
CF_DestinationMap = sys.argv[4] if len(sys.argv) >= 5 else CF_SourceMap

wf = wad.WADFile(CF_Source)

# now, if we want to take a map and put it into a separate wad, what'd we do?
# find a marker lump, then locate the next marker (any), then copy THINGS/LINEDEFS/SIDEDEFS/VERTEXES/SEGS/SSECTORS/NODES/SECTORS/REJECT/BLOCKMAP into another file.

map01 = map.DoomMap()
map01.read(wf, CF_SourceMap.upper())

print('Loaded map of type \"%s\"' % (map01.type))
used_textures = []
used_flats = []

for ms in map01.sidedefs:
	if ms.tex_lower.upper() not in used_textures and ms.tex_lower != '-':
		used_textures.append(ms.tex_lower.upper())
	if ms.tex_upper.upper() not in used_textures and ms.tex_upper != '-':
		used_textures.append(ms.tex_upper.upper())
	if ms.tex_middle.upper() not in used_textures and ms.tex_middle != '-':
		used_textures.append(ms.tex_middle.upper())

for ms in map01.sectors:
	if ms.tex_floor.upper() not in used_flats:
		used_flats.append(ms.tex_floor.upper())
	if ms.tex_ceil.upper() not in used_flats:
		used_flats.append(ms.tex_ceil.upper())

print('The map uses %d textures, %d flats.' % (len(used_textures), len(used_flats)))

# for now just copy the required textures into a new WAD
# (and flats, too)

wf1 = wad.WADFile()

map01.write(wf1, CF_DestinationMap)

wf1.entries.append(wad.WADEntry('FF_START', bytes(), 0))
for flat in used_flats:
	le_num = wf.get_num_for_name(flat)
	if le_num < 0:
		print('Warn: nonexistent flat used: %s' % (flat))
	else:
		le = wf.entries[le_num]
		wf1.entries.append(le)
wf1.entries.append(wad.WADEntry('FF_END', bytes(), 0))

tex0 = tex.DoomTextures()
tex0.read(wf, 'TEXTURE1')

tex1 = tex.DoomTextures()

used_patches = []
for utx in used_textures:
	fnd = False
	for tx in tex0.textures:
		if tx.name == utx:
			tex1.textures.append(tx)
			fnd = True
	if not fnd:
		print('Warn: nonexistent texture used: %s' % (utx))
for tx in tex1.textures:
	for patch in tx.patches:
		if patch.name not in used_patches:
			used_patches.append(patch.name)
for patch in used_patches:
	ent = wf.get_num_for_name(patch)
	if ent < 0:
		print('Warn: nonexistent patch used: %s' % (patch))
	else:
		pe = wf.entries[ent]
		wf1.entries.append(pe)
tex1.write(wf1, 'TEXTURE2')

wf1.write(CF_Destination)