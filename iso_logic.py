import os
import struct
from datetime import datetime
import tempfile
import shutil
import math

class ISOCore:
    def __init__(self):
        self.current_iso_path = None
        self.volume_descriptor = None
        self.root_directory = None
        self.directory_tree = None
        self.iso_modified = False
        self.next_extent_location = 0
        self.iso_file_handle = None
        self.is_joliet = False
        self.boot_image_path = None
        self.efi_boot_image_path = None
        self.boot_emulation_type = 'no_emulation'
        self.init_new_iso()

    def init_new_iso(self):
        self.close_iso()
        self.current_iso_path = None
        self.boot_image_path = None
        self.efi_boot_image_path = None
        self.boot_emulation_type = 'no_emulation'
        self.iso_modified = False
        self.volume_descriptor = {
            'system_id': 'TK_ISO_EDITOR', 'volume_id': 'NEW_ISO',
            'volume_size': 0, 'logical_block_size': 2048,
            'path_table_size': 0, 'root_dir_record': b''
        }
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.directory_tree = {
            'name': '/', 'is_directory': True, 'is_hidden': False,
            'size': 0, 'date': now_str, 'extent_location': 0,
            'children': [], 'parent': None
        }
        self.directory_tree['parent'] = self.directory_tree
        self.root_directory = self.directory_tree

    def close_iso(self):
        if self.iso_file_handle:
            self.iso_file_handle.close()
            self.iso_file_handle = None

    def load_iso(self, file_path):
        self.close_iso()
        try:
            self.iso_file_handle = open(file_path, 'rb')
            self.current_iso_path = file_path
            self.parse_iso_structure()
            self.iso_modified = False
        except FileNotFoundError:
            self.init_new_iso()
            raise IOError(f"ISO file not found at path: {file_path}")
        except Exception as e:
            self.init_new_iso()
            raise e

    def save_iso(self, output_path, use_joliet, use_rock_ridge):
        builder = ISOBuilder(
            root_node=self.directory_tree,
            output_path=output_path,
            volume_id=self.volume_descriptor.get('volume_id', 'TK_ISO_VOL'),
            use_joliet=use_joliet,
            use_rock_ridge=use_rock_ridge,
            boot_image_path=self.boot_image_path,
            efi_boot_image_path=self.efi_boot_image_path,
            boot_emulation_type=self.boot_emulation_type
        )
        builder.build()
        self.current_iso_path = output_path
        self.iso_modified = False

    def parse_iso_structure(self):
        pvd, joliet_svd = None, None
        self.is_joliet = False
        lba = 16
        while True:
            offset = lba * 2048
            self.iso_file_handle.seek(offset)
            vd = self.iso_file_handle.read(2048)
            if len(vd) < 2048: break
            if vd[1:6] != b'CD001': break
            vd_type = vd[0]
            if vd_type == 1: pvd = vd
            elif vd_type == 2:
                if b'%/@' in vd[88:120] or b'%/C' in vd[88:120] or b'%/E' in vd[88:120]:
                    joliet_svd = vd
            elif vd_type == 255: break
            lba += 1

        pvd_data = joliet_svd if joliet_svd else pvd
        if not pvd_data: raise ValueError("No valid Volume Descriptor found.")

        self.is_joliet = joliet_svd is not None
        id_encoding = 'utf-16-be' if self.is_joliet else 'ascii'

        self.volume_descriptor = {
            'system_id': pvd_data[8:40].decode(id_encoding, 'ignore').strip('\x00'),
            'volume_id': pvd_data[40:72].decode(id_encoding, 'ignore').strip('\x00'),
            'volume_size': struct.unpack('<L', pvd_data[80:84])[0],
            'logical_block_size': struct.unpack('<H', pvd_data[128:130])[0],
            'path_table_size': struct.unpack('<L', pvd_data[132:136])[0],
            'root_dir_record': pvd_data[156:190]
        }
        self.root_directory = self.parse_directory_record(self.volume_descriptor['root_dir_record'])
        self.directory_tree = self.build_directory_tree()
        self.calculate_next_extent_location()

    def parse_directory_record(self, record_data):
        if len(record_data) < 33: return None
        record_length = record_data[0]
        if record_length == 0: return None

        file_id_length = record_data[32]
        file_id_bytes = record_data[33:33 + file_id_length]

        system_use_offset = 33 + file_id_length + (1 if file_id_length % 2 == 0 else 0)
        rr_entries = self._parse_susp_entries(record_data[system_use_offset:])

        if self.is_joliet:
            if file_id_bytes == b'\x00': file_id = '.'
            elif file_id_bytes == b'\x01': file_id = '..'
            else: file_id = file_id_bytes.decode('utf-16-be', 'ignore')
        else:
            file_id = file_id_bytes.decode('ascii', 'ignore')

        if 'name' in rr_entries: file_id = rr_entries['name']

        recording_date = record_data[18:25]
        date_str = "Unknown"
        if recording_date[0] > 0:
            try:
                date_str = f"{recording_date[0]+1900:04d}-{recording_date[1]:02d}-{recording_date[2]:02d} {recording_date[3]:02d}:{recording_date[4]:02d}:{recording_date[5]:02d}"
            except: pass

        return {
            'extent_location': struct.unpack('<L', record_data[2:6])[0],
            'data_length': struct.unpack('<L', record_data[10:14])[0],
            'is_directory': bool(record_data[25] & 0x02),
            'is_hidden': bool(record_data[25] & 0x01),
            'file_id': file_id, 'record_length': record_length,
            'recording_date': date_str, 'raw_data': record_data
        }

    def _parse_susp_entries(self, system_use_data):
        entries = {}
        i = 0
        while i < len(system_use_data) - 4:
            try:
                signature, length = system_use_data[i:i+2], system_use_data[i+2]
                if length == 0: break
                data = system_use_data[i+4:i+length]
                if signature == b'NM': entries['name'] = data.decode('ascii', 'ignore')
                i += length
            except: break
        return entries

    def build_directory_tree(self):
        if not self.root_directory: return {}
        tree = {'name': '/', 'is_directory': True, 'children': [], 'parent': None}
        for entry in self.read_directory_entries(self.root_directory['extent_location']):
            if entry['file_id'] in ['.', '..']: continue
            node = {
                'name': entry['file_id'], 'is_directory': entry['is_directory'],
                'is_hidden': entry['is_hidden'], 'size': entry['data_length'],
                'date': entry['recording_date'], 'extent_location': entry['extent_location'],
                'children': [], 'parent': tree
            }
            if entry['is_directory']: self.build_directory_subtree(node)
            tree['children'].append(node)
        return tree

    def build_directory_subtree(self, parent_node):
        for entry in self.read_directory_entries(parent_node['extent_location']):
            if entry['file_id'] in ['.', '..']: continue
            node = {
                'name': entry['file_id'], 'is_directory': entry['is_directory'],
                'is_hidden': entry['is_hidden'], 'size': entry['data_length'],
                'date': entry['recording_date'], 'extent_location': entry['extent_location'],
                'children': [], 'parent': parent_node
            }
            if entry['is_directory'] and len(parent_node['name']) < 50:
                self.build_directory_subtree(node)
            parent_node['children'].append(node)

    def read_directory_entries(self, extent_location):
        entries = []
        if not self.iso_file_handle: return entries
        offset = extent_location * self.volume_descriptor['logical_block_size']
        try:
            self.iso_file_handle.seek(offset)
            directory_data = self.iso_file_handle.read(self.volume_descriptor['logical_block_size'])
        except (IOError, ValueError): return entries

        pos = 0
        while pos < len(directory_data):
            record_length = directory_data[pos]
            if record_length == 0: break
            entry = self.parse_directory_record(directory_data[pos:pos + record_length])
            if entry: entries.append(entry)
            pos += record_length
        return entries

    def get_file_data(self, node):
        if node.get('is_new'): return node.get('file_data', b'')
        if not self.iso_file_handle: return b''
        try:
            offset = node['extent_location'] * self.volume_descriptor['logical_block_size']
            self.iso_file_handle.seek(offset)
            return self.iso_file_handle.read(node['size'])
        except (IOError, ValueError): return b''

    def add_file_to_directory(self, file_path, target_node):
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as f: file_data = f.read()
        except FileNotFoundError:
            raise IOError(f"File not found: {file_path}")
        file_stats = os.stat(file_path)
        new_node = {
            'name': filename, 'is_directory': False, 'is_hidden': False,
            'size': len(file_data), 'date': datetime.fromtimestamp(file_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            'extent_location': 0, 'children': [], 'parent': target_node,
            'file_data': file_data, 'is_new': True
        }
        target_node['children'] = [c for c in target_node['children'] if c['name'].lower() != filename.lower()]
        target_node['children'].append(new_node)
        self.iso_modified = True

    def add_folder_to_directory(self, folder_name, target_node):
        new_node = {
            'name': folder_name, 'is_directory': True, 'is_hidden': False, 'size': 0,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'extent_location': 0,
            'children': [], 'parent': target_node, 'is_new': True
        }
        target_node['children'].append(new_node)
        self.iso_modified = True

    def remove_node(self, node_to_remove):
        parent = node_to_remove.get('parent')
        if parent:
            parent['children'] = [c for c in parent['children'] if id(c) != id(node_to_remove)]
            self.iso_modified = True

    def calculate_next_extent_location(self):
        max_extent = 0
        def find_max_extent(node):
            nonlocal max_extent
            if node['extent_location'] > max_extent: max_extent = node['extent_location']
            for child in node.get('children', []): find_max_extent(child)
        if self.directory_tree: find_max_extent(self.directory_tree)
        self.next_extent_location = max_extent + 10

def _pack_both_endian_16(n):
    return struct.pack('<H', n) + struct.pack('>H', n)
def _pack_both_endian_32(n):
    return struct.pack('<L', n) + struct.pack('>L', n)
def _format_pvd_date(dt=None):
    if dt is None: dt = datetime.now()
    return dt.strftime('%Y%m%d%H%M%S00').encode('ascii') + b'\x00'
def _format_dir_date(dt=None):
    if dt is None: dt = datetime.now()
    return struct.pack('BBBBBBb', dt.year - 1900, dt.month, dt.day, dt.hour, dt.minute, dt.second, 0)
def _format_str_d(s, length):
    s = s.upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
    s = ''.join(c for c in s if c in allowed)
    return s.ljust(length, ' ').encode('ascii')
def _format_str_a(s, length):
    s = s.upper()
    allowed = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_!\"%&'()*+,-./:;<=>?"
    s = ''.join(c for c in s if c in allowed)
    return s.ljust(length, ' ').encode('ascii')

class ISOBuilder:
    def __init__(self, root_node, output_path, volume_id="TK_ISO_VOL",
                 use_joliet=True, use_rock_ridge=True,
                 boot_image_path=None, efi_boot_image_path=None,
                 boot_emulation_type='no_emulation'):
        self.root_node = root_node
        self.output_path = output_path
        self.volume_id = volume_id
        self.use_joliet = use_joliet
        self.use_rock_ridge = use_rock_ridge
        self.boot_image_path = boot_image_path
        self.efi_boot_image_path = efi_boot_image_path
        self.boot_emulation_type = boot_emulation_type
        self.logical_block_size = 2048
        self.next_lba = 0
        self.temp_file = None

    def build(self):
        self.temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        try:
            # Reserve space for system area
            self.temp_file.seek(16 * self.logical_block_size)
            self.next_lba = 16

            # Volume Descriptor LBA locations
            pvd_lba = self.next_lba; self.next_lba += 1
            bvd_lba = 0
            if self.boot_image_path or self.efi_boot_image_path:
                bvd_lba = self.next_lba; self.next_lba += 1
            svd_lba = self.next_lba if self.use_joliet else 0; self.next_lba += (1 if self.use_joliet else 0)
            terminator_lba = self.next_lba; self.next_lba += 1

            # Add boot images to the file tree
            boot_image_nodes = self._add_boot_images()

            pvd_path_records, file_map = self._layout_hierarchy(is_joliet=False)

            # Now that the boot images have extents, we can create the catalog
            boot_catalog_lba = 0
            if boot_image_nodes:
                boot_entries = []
                if 'bios' in boot_image_nodes:
                    # platform_id, boot_media_type, load_segment, sector_count, lba
                    boot_entries.append((0x00, 0, 0, 4, boot_image_nodes['bios']['extent_location']))
                if 'efi' in boot_image_nodes:
                    # For EFI, the load segment is 0 and sector count is file size / 512
                    sector_count = math.ceil(boot_image_nodes['efi']['size'] / 512)
                    boot_entries.append((0xef, 0, 0, sector_count, boot_image_nodes['efi']['extent_location']))

                boot_catalog_data = self._generate_boot_catalog(boot_entries)
                boot_catalog_lba = self._write_data_block(boot_catalog_data)

            # Generate and write path tables and directory records
            pvd_l_path, pvd_m_path = self._generate_path_tables(pvd_path_records, False)
            pvd_l_path_lba = self._write_data_block(pvd_l_path)
            pvd_m_path_lba = self._write_data_block(pvd_m_path)
            self._write_directory_records_recursively(self.root_node, False)

            if self.use_joliet:
                svd_path_records, _ = self._layout_hierarchy(is_joliet=True, file_map=file_map)
                svd_l_path, svd_m_path = self._generate_path_tables(svd_path_records, True)
                svd_l_path_lba = self._write_data_block(svd_l_path)
                svd_m_path_lba = self._write_data_block(svd_m_path)
                self._write_directory_records_recursively(self.root_node, True)

            volume_size_in_blocks = self.next_lba

            # Generate and write Volume Descriptors
            pvd_data = self._generate_pvd(volume_size_in_blocks, pvd_l_path_lba, pvd_m_path_lba, len(pvd_l_path), False, boot_catalog_lba)
            self._write_data_at_lba(pvd_lba, pvd_data)

            if self.boot_image_path or self.efi_boot_image_path:
                bvd_data = self._generate_boot_record(boot_catalog_lba)
                self._write_data_at_lba(bvd_lba, bvd_data)

            if self.use_joliet:
                svd_data = self._generate_pvd(volume_size_in_blocks, svd_l_path_lba, svd_m_path_lba, len(svd_l_path), True)
                self._write_data_at_lba(svd_lba, svd_data)

            terminator_data = self._generate_terminator()
            self._write_data_at_lba(terminator_lba, terminator_data)

        finally:
            if self.temp_file:
                self.temp_file.close()
                shutil.move(self.temp_file.name, self.output_path)

    def _add_boot_images(self):
        nodes = {}
        # Handle BIOS boot image
        if self.boot_image_path and os.path.exists(self.boot_image_path):
            try:
                with open(self.boot_image_path, 'rb') as f:
                    boot_image_data = f.read()
            except FileNotFoundError:
                raise IOError(f"Boot image not found: {self.boot_image_path}")
            bios_node = {
                'name': 'BOOT.IMG',
                'is_directory': False, 'is_hidden': True, 'size': len(boot_image_data),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'extent_location': 0,
                'children': [], 'parent': self.root_node, 'file_data': boot_image_data, 'is_new': True
            }
            self.root_node['children'].insert(0, bios_node)
            nodes['bios'] = bios_node

        # Handle EFI boot image
        if self.efi_boot_image_path and os.path.exists(self.efi_boot_image_path):
            try:
                with open(self.efi_boot_image_path, 'rb') as f:
                    efi_boot_image_data = f.read()
            except FileNotFoundError:
                raise IOError(f"EFI boot image not found: {self.efi_boot_image_path}")
            efi_node = {
                'name': 'EFI.IMG',
                'is_directory': False, 'is_hidden': True, 'size': len(efi_boot_image_data),
                'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'extent_location': 0,
                'children': [], 'parent': self.root_node, 'file_data': efi_boot_image_data, 'is_new': True
            }
            self.root_node['children'].insert(0, efi_node)
            nodes['efi'] = efi_node

        return nodes

    def _write_data_at_lba(self, lba, data):
        self.temp_file.seek(lba * self.logical_block_size)
        self.temp_file.write(data)

    def _write_data_block(self, data):
        lba = self.next_lba
        self._write_data_at_lba(lba, data)
        self.next_lba += math.ceil(len(data) / self.logical_block_size) if data else 1
        return lba

    def _get_short_name(self, name):
        name = name.upper()
        allowed_chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_"
        name = ''.join(c for c in name if c in allowed_chars)
        parts = name.split('.')
        if len(parts) > 1 and parts[-1]:
            base = ''.join(parts[:-1])
            ext = parts[-1]
            return base[:8] + '.' + ext[:3]
        else:
            return name[:11].split('.')[0][:8]

    def _layout_hierarchy(self, is_joliet, file_map=None):
        path_table_records = []
        if file_map is None: file_map = {}
        def _recursive_layout(node, parent_dir_num):
            dir_num = len(path_table_records) + 1
            path_table_records.append({'node': node, 'parent_dir_num': parent_dir_num})
            for child in sorted(node['children'], key=lambda x: x['name']):
                if child['is_directory']: _recursive_layout(child, dir_num)
            if not is_joliet:
                for child in sorted(node['children'], key=lambda x: x['name']):
                    if not child['is_directory']:
                        child_id = id(child)
                        if child_id not in file_map:
                            file_data = child.get('file_data', b'')
                            child['extent_location'] = self._write_data_block(file_data)
                            file_map[child_id] = child['extent_location']
                        else: child['extent_location'] = file_map[child_id]
            else:
                 for child in sorted(node['children'], key=lambda x: x['name']):
                    if not child['is_directory']: child['extent_location'] = file_map[id(child)]
            dir_records_data = self._generate_directory_records_for_node(node, is_joliet)
            data_len_key = 'joliet_data_length' if is_joliet else 'pvd_data_length'
            extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'
            node[data_len_key] = len(dir_records_data)
            node[extent_loc_key] = self._write_data_block(b'\x00' * node[data_len_key])
        _recursive_layout(self.root_node, 1)
        return path_table_records, file_map

    def _generate_path_tables(self, path_table_records, is_joliet):
        path_table_records.sort(key=lambda r: self.get_node_path(r['node']))
        dir_num_map = {self.get_node_path(r['node']): i + 1 for i, r in enumerate(path_table_records)}
        l_table, m_table = bytearray(), bytearray()
        for record in path_table_records:
            node, path = record['node'], self.get_node_path(record['node'])
            parent_path = os.path.dirname(path).replace('\\', '/') if path != '/' else '/'
            parent_dir_num = dir_num_map.get(parent_path, 1)
            extent_loc = node['joliet_extent_location' if is_joliet else 'pvd_extent_location']
            name = self._get_short_name(node['name']) if not is_joliet else node['name']
            dir_id = b'\x00' if name == '/' else name.encode('utf-16-be' if is_joliet else 'ascii')
            id_len = len(dir_id)
            l_rec = struct.pack('<BB<L<H', id_len, 0, extent_loc, parent_dir_num) + dir_id
            if id_len % 2 != 0: l_rec += b'\x00'
            l_table.extend(l_rec)
            m_rec = struct.pack('<BB>L>H', id_len, 0, extent_loc, parent_dir_num) + dir_id
            if id_len % 2 != 0: m_rec += b'\x00'
            m_table.extend(m_rec)
        return bytes(l_table), bytes(m_table)

    def _write_directory_records_recursively(self, node, is_joliet):
        records_data = self._generate_directory_records_for_node(node, is_joliet)
        extent_loc_key = 'joliet_extent_location' if is_joliet else 'pvd_extent_location'
        self._write_data_at_lba(node[extent_loc_key], records_data)
        for child in node['children']:
            if child['is_directory']:
                self._write_directory_records_recursively(child, is_joliet)

    def _generate_directory_records_for_node(self, node, is_joliet):
        all_records = bytearray()
        all_records.extend(self._create_dir_record(node, is_joliet, is_self=True))
        all_records.extend(self._create_dir_record(node.get('parent', node), is_joliet, is_parent=True))
        for child in sorted(node['children'], key=lambda x: x['name']):
            all_records.extend(self._create_dir_record(child, is_joliet))
        return bytes(all_records)

    def _create_dir_record(self, node, is_joliet, is_self=False, is_parent=False):
        file_flags = 0x02 if node.get('is_directory') else 0
        if node.get('is_hidden', False): file_flags |= 0x01
        extent_loc = node.get('joliet_extent_location' if is_joliet else 'pvd_extent_location', node.get('extent_location', 0))
        data_len = node.get('joliet_data_length' if is_joliet else 'pvd_data_length', 0) if node.get('is_directory') else node.get('size', 0)
        system_use_data = b''
        if is_self: file_id_bytes = b'\x00'
        elif is_parent: file_id_bytes = b'\x01'
        else:
            if is_joliet: file_id_bytes = node['name'].encode('utf-16-be')
            else:
                short_name = self._get_short_name(node['name'])
                if not node['is_directory']: short_name += ';1'
                file_id_bytes = short_name.encode('ascii')
                if self.use_rock_ridge and node['name'].upper() != short_name.split(';')[0]:
                    nm_data = node['name'].encode('ascii', 'ignore')
                    system_use_data += b'NM' + struct.pack('<BB', len(nm_data) + 5, 1) + nm_data
        file_id_len = len(file_id_bytes)
        record_len = 33 + file_id_len + len(system_use_data)
        if record_len % 2 != 0: record_len += 1
        rec = bytearray(record_len)
        struct.pack_into('<B', rec, 0, record_len)
        rec[2:10] = _pack_both_endian_32(extent_loc)
        rec[10:18] = _pack_both_endian_32(data_len)
        rec[18:25] = _format_dir_date(datetime.strptime(node['date'], "%Y-%m-%d %H:%M:%S") if node.get('date') else datetime.now())
        struct.pack_into('<B', rec, 25, file_flags)
        rec[28:32] = _pack_both_endian_16(1)
        struct.pack_into('<B', rec, 32, file_id_len)
        rec[33:33 + file_id_len] = file_id_bytes
        if system_use_data:
            offset = 33 + file_id_len + (1 if file_id_len % 2 == 0 else 0)
            rec[offset:offset+len(system_use_data)] = system_use_data
        return bytes(rec)

    def _generate_pvd(self, volume_size, lba_l, lba_m, path_table_size, is_joliet=False, boot_catalog_lba=0):
        vd = bytearray(self.logical_block_size)
        vd_type = 2 if is_joliet else 1
        encoding = 'utf-16-be' if is_joliet else 'ascii'
        root_record_data = self._create_dir_record(self.root_node, is_joliet, is_self=True)

        vd[0:1] = struct.pack('B', vd_type)
        vd[1:6] = b'CD001'; vd[6:7] = b'\x01'

        # Pointer to Boot Catalog in PVD (El Torito)
        if not is_joliet and boot_catalog_lba > 0:
            vd[73:77] = struct.pack('<L', boot_catalog_lba)

        if is_joliet: vd[88:91] = b'%/@'
        vd[8:40] = _format_str_a("PYTHON TK ISO EDITOR", 32)
        vd[40:72] = self.volume_id.encode(encoding, 'ignore').ljust(32, b'\x00' if is_joliet else b' ')
        vd[80:88] = _pack_both_endian_32(volume_size)
        vd[120:124] = _pack_both_endian_16(1)
        vd[124:128] = _pack_both_endian_16(1)
        vd[128:132] = _pack_both_endian_16(self.logical_block_size)
        vd[132:140] = _pack_both_endian_32(path_table_size)
        vd[140:144] = struct.pack('<L', lba_l)
        vd[148:152] = struct.pack('>L', lba_m)
        vd[156:190] = root_record_data[:34]
        vd[190:318] = "ISO_SET".encode(encoding, 'ignore').ljust(128, b'\x00' if is_joliet else b' ')
        vd[881:882] = b'\x01'
        return vd

    def _generate_boot_record(self, boot_catalog_lba):
        # El Torito Boot Volume Descriptor
        bvd = bytearray(self.logical_block_size)
        bvd[0] = 0 # Boot Record
        bvd[1:6] = b'CD001'
        bvd[6] = 1 # Version
        bvd[7:39] = b'EL TORITO SPECIFICATION'
        bvd[72:76] = struct.pack('<L', boot_catalog_lba)
        return bvd

    def _generate_boot_catalog(self, boot_entries):
        catalog = bytearray(self.logical_block_size)
        offset = 0

        # Validation Entry (always first)
        catalog[offset] = 1  # Header ID
        catalog[offset+1] = 0 # Platform ID (x86) - this is for the validation entry itself
        catalog[offset+4:offset+32] = b'ISO EDITOR BOOT'

        checksum = 0
        for i in range(0, 32, 4):
            checksum += struct.unpack('<L', catalog[offset+i:offset+i+4])[0]
        checksum = (0x100000000 - checksum) & 0xFFFFFFFF
        struct.pack_into('<L', catalog, offset+28, checksum)
        catalog[offset+30] = 0x55
        catalog[offset+31] = 0xAA
        offset += 32

        # Create Initial/Default and Section Entries for each boot image
        is_first_entry = True
        for platform_id, boot_media_type, load_segment, sector_count, lba in boot_entries:
            if is_first_entry:
                # Initial/Default Entry
                catalog[offset] = 0x88 # Bootable
                is_first_entry = False
            else:
                # Section Entry
                catalog[offset] = 0x91 # Bootable (more entries follow) if not the last, 0x90 otherwise.
                                     # Simplified for now, assuming this logic will be refined.

            catalog[offset+1] = platform_id
            struct.pack_into('<H', catalog, offset+2, 1) # Number of bootable entries for this spec
            # No ID string for entries other than validation

            # Entry details
            struct.pack_into('<H', catalog, offset+4, load_segment)
            catalog[offset+6] = boot_media_type
            struct.pack_into('<H', catalog, offset+8, sector_count)
            struct.pack_into('<L', catalog, offset+12, lba)
            offset += 32

        return catalog

    def _generate_terminator(self):
        terminator = bytearray(self.logical_block_size)
        terminator[0:1] = b'\xff'; terminator[1:6] = b'CD001'; terminator[6:7] = b'\x01'
        return terminator

    def get_node_path(self, node):
        if not node.get('parent'): return '/'
        path_parts = []
        current = node
        while current and current.get('parent'):
            path_parts.append(current['name'])
            current = current['parent']
        return '/' + '/'.join(reversed(path_parts))
