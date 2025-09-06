import os
import struct
from datetime import datetime
import tempfile
import shutil
import math
import logging

logger = logging.getLogger(__name__)

class ISOCore:
    """
    Core logic for handling ISO file structures.

    This class manages the in-memory representation of an ISO file,
    including loading from an existing ISO, parsing its structure,
    modifying the file tree, and saving it back to a new ISO file.
    """
    def __init__(self):
        """Initializes the ISOCore instance with a new, empty ISO structure."""
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
        """Initializes or resets the core to a new, empty ISO structure."""
        logger.info("Initializing new ISO structure.")
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
        """Closes the currently open ISO file handle, if one exists."""
        if self.iso_file_handle:
            logger.info(f"Closing ISO file: {self.current_iso_path}")
            try:
                self.iso_file_handle.close()
            except IOError as e:
                logger.error(f"Error closing ISO file: {e}")
            self.iso_file_handle = None

    def load_iso(self, file_path):
        """
        Loads an ISO file from the given path and parses its structure.

        Args:
            file_path (str): The path to the ISO file to load.

        Raises:
            IOError: If the file is not found or another I/O error occurs.
            ValueError: If the ISO structure is invalid or cannot be parsed.
        """
        logger.info(f"Loading ISO from path: {file_path}")
        self.close_iso()
        try:
            self.iso_file_handle = open(file_path, 'rb')
            self.current_iso_path = file_path
            self.parse_iso_structure()
            self.iso_modified = False
        except FileNotFoundError:
            self.init_new_iso()
            logger.error(f"ISO file not found at path: {file_path}")
            raise IOError(f"ISO file not found at path: {file_path}")
        except Exception as e:
            self.init_new_iso()
            logger.exception(f"An unexpected error occurred while loading the ISO: {e}")
            raise

    def save_iso(self, output_path, use_joliet, use_rock_ridge):
        """
        Saves the current in-memory ISO structure to a new file.

        Args:
            output_path (str): The path to save the new ISO file to.
            use_joliet (bool): Whether to use Joliet extensions for long filenames.
            use_rock_ridge (bool): Whether to use Rock Ridge extensions.
        """
        logger.info(f"Saving ISO to path: {output_path}")
        try:
            builder = ISOBuilder(
                root_node=self.directory_tree,
                output_path=output_path,
                volume_id=self.volume_descriptor.get('volume_id', 'TK_ISO_VOL'),
                use_joliet=use_joliet,
                use_rock_ridge=use_rock_ridge,
                boot_image_path=self.boot_image_path,
                efi_boot_image_path=self.efi_boot_image_path,
                boot_emulation_type=self.boot_emulation_type,
                core=self
            )
            builder.build()
            self.current_iso_path = output_path
            self.iso_modified = False
        except Exception as e:
            logger.exception(f"Failed to save ISO to {output_path}: {e}")
            raise

    def parse_iso_structure(self):
        """
        Parses the volume descriptors and file system of the loaded ISO.

        Raises:
            ValueError: If no valid Primary Volume Descriptor is found.
        """
        logger.debug("Starting to parse ISO structure.")
        try:
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
            logger.info(f"ISO uses Joliet extensions: {self.is_joliet}")

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
            logger.debug("Finished parsing ISO structure.")
        except struct.error as e:
            logger.exception(f"Struct error while parsing ISO structure: {e}")
            raise ValueError("Invalid ISO structure.") from e
        except Exception as e:
            logger.exception(f"An unexpected error occurred during ISO parsing: {e}")
            raise

    def parse_directory_record(self, record_data):
        """
        Parses a single directory record.

        Args:
            record_data (bytes): The raw byte data of the directory record.

        Returns:
            dict or None: A dictionary representing the directory record,
                          or None if the record is empty or invalid.
        """
        try:
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
        except (struct.error, IndexError) as e:
            logger.error(f"Failed to parse directory record: {e}")
            return None

    def _parse_susp_entries(self, system_use_data):
        """
        Parses System Use Sharing Protocol (SUSP) and Rock Ridge entries.

        Args:
            system_use_data (bytes): The system use area from a directory record.

        Returns:
            dict: A dictionary of parsed Rock Ridge entries (e.g., 'name').
        """
        entries = {}
        i = 0
        while i < len(system_use_data) - 4:
            try:
                signature, length = system_use_data[i:i+2], system_use_data[i+2]
                if length == 0: break
                data = system_use_data[i+4:i+length]
                if signature == b'NM': entries['name'] = data.decode('ascii', 'ignore')
                i += length
            except Exception as e:
                logger.error(f"Error parsing SUSP entries: {e}")
                break
        return entries

    def build_directory_tree(self):
        """
        Builds the in-memory directory tree from the parsed root directory.

        Returns:
            dict: The root node of the constructed directory tree.
        """
        logger.debug("Building directory tree from parsed records.")
        if not self.root_directory: return {}
        tree = {
            'name': '/', 'is_directory': True, 'children': [], 'parent': None,
            'extent_location': self.root_directory.get('extent_location', 0),
            'date': self.root_directory.get('recording_date', '')
        }
        tree['parent'] = tree
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
        """
        Recursively builds a subtree for a given directory node.

        Args:
            parent_node (dict): The parent directory node to build the subtree from.
        """
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
        """
        Reads all directory entries from a given extent.

        Args:
            extent_location (int): The LBA of the extent containing the directory records.

        Returns:
            list: A list of directory record dictionaries.
        """
        entries = []
        if not self.iso_file_handle: return entries
        offset = extent_location * self.volume_descriptor['logical_block_size']
        try:
            self.iso_file_handle.seek(offset)
            directory_data = self.iso_file_handle.read(self.volume_descriptor['logical_block_size'])
        except (IOError, ValueError) as e:
            logger.error(f"Error reading directory entries at LBA {extent_location}: {e}")
            return entries

        pos = 0
        while pos < len(directory_data):
            try:
                record_length = directory_data[pos]
                if record_length == 0: break
                entry = self.parse_directory_record(directory_data[pos:pos + record_length])
                if entry: entries.append(entry)
                pos += record_length
            except IndexError:
                logger.error("Reached end of directory data unexpectedly.")
                break
        return entries

    def get_file_data(self, node):
        """
        Retrieves the data for a given file node.

        Args:
            node (dict): The file node to retrieve data for.

        Returns:
            bytes: The file data.
        """
        if node.get('is_new'): return node.get('file_data', b'')
        if not self.iso_file_handle: return b''
        try:
            offset = node['extent_location'] * self.volume_descriptor['logical_block_size']
            self.iso_file_handle.seek(offset)
            return self.iso_file_handle.read(node['size'])
        except (IOError, ValueError) as e:
            logger.error(f"Error getting file data for {node.get('name')}: {e}")
            return b''

    def add_file_to_directory(self, file_path, target_node):
        """
        Adds a file from the local filesystem to a directory in the ISO structure.

        Args:
            file_path (str): The path to the local file to add.
            target_node (dict): The target directory node in the ISO tree.
        """
        logger.info(f"Adding file '{file_path}' to '{self.get_node_path(target_node)}'")
        filename = os.path.basename(file_path)
        try:
            with open(file_path, 'rb') as f: file_data = f.read()
            file_stats = os.stat(file_path)
        except (FileNotFoundError, IOError) as e:
            logger.error(f"Error adding file {file_path}: {e}")
            raise IOError(f"File not found or unreadable: {file_path}") from e

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
        """
        Adds a new, empty folder to a directory in the ISO structure.

        Args:
            folder_name (str): The name of the new folder.
            target_node (dict): The target directory node in the ISO tree.
        """
        logger.info(f"Adding folder '{folder_name}' to '{self.get_node_path(target_node)}'")
        new_node = {
            'name': folder_name, 'is_directory': True, 'is_hidden': False, 'size': 0,
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'extent_location': 0,
            'children': [], 'parent': target_node, 'is_new': True
        }
        target_node['children'].append(new_node)
        self.iso_modified = True

    def remove_node(self, node_to_remove):
        """
        Removes a file or folder node from the directory tree.

        Args:
            node_to_remove (dict): The node to remove.
        """
        parent = node_to_remove.get('parent')
        if parent:
            logger.info(f"Removing node '{node_to_remove['name']}' from '{self.get_node_path(parent)}'")
            parent['children'] = [c for c in parent['children'] if id(c) != id(node_to_remove)]
            self.iso_modified = True

    def calculate_next_extent_location(self):
        """Calculates the next available LBA for writing new data."""
        max_extent = 0
        def find_max_extent(node):
            nonlocal max_extent
            if node.get('extent_location', 0) > max_extent:
                max_extent = node['extent_location']
            for child in node.get('children', []):
                find_max_extent(child)
        if self.directory_tree:
            find_max_extent(self.directory_tree)
        self.next_extent_location = max_extent + 10
        logger.debug(f"Calculated next available extent location: {self.next_extent_location}")

class ISOBuilder:
    """
    Builds an ISO 9660 file from an in-memory directory tree.
    """
    def __init__(self, root_node, output_path, volume_id="TK_ISO_VOL",
                 use_joliet=True, use_rock_ridge=True,
                 boot_image_path=None, efi_boot_image_path=None,
                 boot_emulation_type='no_emulation', core=None):
        """
        Initializes the ISOBuilder.

        Args:
            root_node (dict): The root node of the directory tree to build.
            output_path (str): The path to write the output ISO file to.
            volume_id (str): The volume ID for the ISO.
            use_joliet (bool): Whether to include Joliet extensions.
            use_rock_ridge (bool): Whether to include Rock Ridge extensions.
            boot_image_path (str, optional): Path to the BIOS boot image.
            efi_boot_image_path (str, optional): Path to the EFI boot image.
            boot_emulation_type (str): The El Torito boot emulation type.
            core (ISOCore, optional): The ISOCore instance, for accessing file data.
        """
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
        self.core = core

    def build(self):
        """
        Builds the ISO file and writes it to the output path.
        """
        logger.info("Starting ISO build process.")
        self.temp_file = tempfile.NamedTemporaryFile(mode='wb', delete=False)
        try:
            # ... (build logic)
            logger.info("ISO build process completed successfully.")
        finally:
            if self.temp_file:
                self.temp_file.close()
                shutil.move(self.temp_file.name, self.output_path)
                logger.info(f"Temporary file moved to {self.output_path}")

    def _add_boot_images(self):
        """Adds boot images to the root directory if they exist."""
        # ... (implementation)

    def _write_data_at_lba(self, lba, data):
        """Writes a block of data at a specific LBA."""
        # ... (implementation)

    def _write_data_block(self, data):
        """
        Writes a block of data to the next available LBA, padding it to a full sector.

        Args:
            data (bytes): The data to write.

        Returns:
            int: The LBA where the data was written.
        """
        lba = self.next_lba
        num_blocks = math.ceil(len(data) / self.logical_block_size) if data else 1
        padded_data = data.ljust(num_blocks * self.logical_block_size, b'\x00')
        self._write_data_at_lba(lba, padded_data)
        self.next_lba += num_blocks
        return lba

    def _get_short_name(self, name):
        """Converts a long filename to a DOS-compatible 8.3 filename."""
        # ... (implementation)

    def _layout_hierarchy(self, is_joliet, file_map=None):
        """
        Lays out the file and directory hierarchy, writing file data and
        calculating directory record sizes.

        Args:
            is_joliet (bool): True if laying out for a Joliet SVD.
            file_map (dict, optional): A map to reuse file extents between PVD and SVD.

        Returns:
            tuple: A tuple containing the path table records and the file map.
        """
        # ... (implementation)

    def _generate_path_tables(self, path_table_records, is_joliet):
        """
        Generates the little-endian and big-endian path tables.

        Args:
            path_table_records (list): A list of path table record dictionaries.
            is_joliet (bool): True if generating for a Joliet SVD.

        Returns:
            tuple: A tuple containing the little-endian and big-endian path table data.
        """
        # ... (implementation)

    def _write_directory_records_recursively(self, node, is_joliet):
        """Recursively writes the directory records for a node and its children."""
        # ... (implementation)

    def _generate_directory_records_for_node(self, node, is_joliet):
        """Generates the full directory record data for a single directory."""
        # ... (implementation)

    def _create_dir_record(self, node, is_joliet, is_self=False, is_parent=False):
        """Creates a single directory record."""
        # ... (implementation)

    def _generate_pvd(self, volume_size, lba_l, lba_m, path_table_size, is_joliet=False, boot_catalog_lba=0):
        """Generates a Primary or Supplementary Volume Descriptor."""
        # ... (implementation)

    def _generate_boot_record(self, boot_catalog_lba):
        """Generates the El Torito Boot Volume Descriptor."""
        # ... (implementation)

    def _generate_boot_catalog(self, boot_entries):
        """Generates the El Torito boot catalog."""
        # ... (implementation)

    def _generate_terminator(self):
        """Generates a Volume Descriptor Set Terminator."""
        # ... (implementation)

    def get_node_path(self, node):
        """
        Gets the full path string for a given node in the directory tree.

        Args:
            node (dict): The node to get the path for.

        Returns:
            str: The full path of the node.
        """
        if not node.get('parent') or node.get('parent') is node:
            return '/'
        path_parts = []
        current = node
        while current and current.get('parent') and current.get('parent') is not current:
            path_parts.append(current['name'])
            current = current['parent']
        return '/' + '/'.join(reversed(path_parts))
