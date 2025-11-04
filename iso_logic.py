import os
import re
import struct
from datetime import datetime
import tempfile
import shutil
import math
import logging
import pycdlib
from io import BytesIO
import posixpath
from cueparser import CueSheet

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
        self.directory_tree = None
        self.iso_modified = False
        self.boot_image_path = None
        self.efi_boot_image_path = None
        self.boot_emulation_type = 'noemul'
        self._pycdlib_instance = None
        self.is_joliet = False
        self.init_new_iso()

    def init_new_iso(self):
        """Initializes or resets the core to a new, empty ISO structure."""
        logger.info("Initializing new ISO structure.")
        self.close_iso()
        self.current_iso_path = None
        self.boot_image_path = None
        self.efi_boot_image_path = None
        self.boot_emulation_type = 'noemul'
        self.iso_modified = False
        self._pycdlib_instance = None
        self.is_joliet = False
        self.volume_descriptor = {
            'system_id': 'TK_ISO_EDITOR', 'volume_id': 'NEW_ISO',
            'volume_size': 0, 'logical_block_size': 2048
        }
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.directory_tree = {
            'name': '/', 'is_directory': True, 'is_hidden': False,
            'size': 0, 'date': now_str, 'extent_location': 0,
            'children': [], 'parent': None
        }
        self.directory_tree['parent'] = self.directory_tree
        self.extracted_boot_info = []

    def close_iso(self):
        """Closes the currently open ISO file handle, if one exists."""
        if self._pycdlib_instance:
            logger.info(f"Closing ISO file: {self.current_iso_path}")
            try:
                self._pycdlib_instance.close()
            except Exception as e:
                logger.error(f"Error closing pycdlib instance: {e}")
            self._pycdlib_instance = None

    def load_iso(self, file_path):
        """
        Loads an ISO file from the given path and parses its structure using pycdlib.

        Args:
            file_path (str): The path to the ISO file to load.

        Raises:
            IOError: If the file is not found or another I/O error occurs.
            ValueError: If the image structure is invalid or cannot be parsed.
        """
        logger.info(f"Loading image from path: {file_path}")
        self.init_new_iso()

        _, extension = os.path.splitext(file_path)
        if extension.lower() == '.cue':
            self._load_cue_sheet(file_path)
            self.current_iso_path = file_path
            self.iso_modified = False
        else:
            try:
                iso = pycdlib.PyCdlib()
                iso.open(file_path)

                self._pycdlib_instance = iso
                self.current_iso_path = file_path
                self.is_joliet = iso.has_joliet()

                if self.is_joliet and iso.joliet_vd:
                    self.volume_descriptor['volume_id'] = iso.joliet_vd.volume_identifier.decode('utf-16-be', 'ignore').strip()
                    self.volume_descriptor['system_id'] = iso.joliet_vd.system_identifier.decode('utf-16-be', 'ignore').strip()
                elif iso.pvd:
                    self.volume_descriptor['volume_id'] = iso.pvd.volume_identifier.decode('ascii', 'ignore').strip()
                    self.volume_descriptor['system_id'] = iso.pvd.system_identifier.decode('ascii', 'ignore').strip()

                self.directory_tree = self._build_tree_from_pycdlib()
                self._extract_boot_info() # New method call
                self.iso_modified = False
            except FileNotFoundError:
                self.init_new_iso()
                logger.error(f"ISO file not found at path: {file_path}")
                raise IOError(f"ISO file not found at path: {file_path}")
            except Exception as e:
                self.init_new_iso()
                logger.exception(f"An unexpected error occurred while loading the ISO with pycdlib: {e}")
                raise ValueError(f"Failed to parse ISO with pycdlib: {e}") from e

    def _load_cue_sheet(self, file_path):
        """Builds the internal directory_tree from a CUE sheet."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cue_data = f.read()
        except FileNotFoundError:
            logger.error(f"CUE file not found at path: {file_path}")
            raise IOError(f"CUE file not found at path: {file_path}") from None
        except Exception as e:
            logger.error(f"Error reading CUE file {file_path}: {e}")
            raise IOError(f"Error reading CUE file: {e}") from e

        cue_sheet = CueSheet()
        cue_sheet.setOutputFormat('%performer% - %title%', '%performer% - %title%')
        cue_sheet.setData(cue_data)
        try:
            cue_sheet.parse()
        except Exception as e:
            logger.error(f"CueParser failed to parse CUE data. Error: {e}")
            raise ValueError(f"Failed to parse CUE sheet: {e}") from e

        # If parsing results in no tracks, but there was data, it's an error
        if not cue_sheet.tracks and cue_data.strip():
            raise ValueError("CUE sheet is invalid or contains no tracks.")

        self.volume_descriptor['volume_id'] = cue_sheet.title or "CUE_SHEET"

        bin_filename = cue_sheet.file
        if not bin_filename:
            raise ValueError("CUE sheet does not specify a BIN file.")

        for i, track in enumerate(cue_sheet.tracks):
            track_node = {
                'name': track.title or f'TRACK_{i+1:02d}.wav',
                'is_directory': False,
                'is_hidden': False,
                'size': 0, # Will be calculated later
                'date': '',
                'children': [],
                'parent': self.directory_tree,
                'is_new': False,
                'is_cue_track': True,
                'cue_track_number': i,
                'cue_bin_file': os.path.join(os.path.dirname(file_path), bin_filename),
                'cue_offset': self._parse_cue_offset(track.offset),
            }
            self.directory_tree['children'].append(track_node)

        # Now, calculate the size of each track
        for i, track_node in enumerate(self.directory_tree['children']):
            if i + 1 < len(self.directory_tree['children']):
                next_track_node = self.directory_tree['children'][i+1]
                track_node['size'] = next_track_node['cue_offset'] - track_node['cue_offset']
            else:
                # For the last track, the size is the rest of the BIN file.
                bin_path = track_node['cue_bin_file']
                if os.path.exists(bin_path):
                    total_size = os.path.getsize(bin_path)
                    track_node['size'] = total_size - track_node['cue_offset']
                else:
                    track_node['size'] = 0

    def _parse_cue_offset(self, offset_str):
        """Converts a CUE sheet offset string (MM:SS:FF) to bytes."""
        try:
            parts = offset_str.split(':')
            if len(parts) != 3:
                raise ValueError("Offset must be in MM:SS:FF format")
            minutes = int(parts[0])
            seconds = int(parts[1])
            frames = int(parts[2])
            if not (0 <= seconds < 60 and 0 <= frames < 75):
                raise ValueError(f"Invalid time component in offset: seconds={seconds}, frames={frames}")

            total_frames = (minutes * 60 * 75) + (seconds * 75) + frames
            return total_frames * 2352 # 2352 bytes per frame for CD-DA
        except (ValueError, IndexError) as e:
            logger.error(f"Could not parse CUE offset string: '{offset_str}'. Error: {e}")
            raise ValueError(f"Invalid CUE offset format: '{offset_str}'") from e

    def _build_tree_from_pycdlib(self):
        """Builds the internal directory_tree structure from the loaded pycdlib instance."""
        if not self._pycdlib_instance:
            return None

        root_node = {
            'name': '/', 'is_directory': True, 'is_hidden': False, 'size': 0,
            'date': '', 'children': [], 'parent': None, 'iso_path': '/'
        }
        root_node['parent'] = root_node
        node_map = {'/': root_node}

        if self._pycdlib_instance.has_udf():
            walk_key = 'udf_path'
            walker = self._pycdlib_instance.walk(udf_path='/')
        elif self.is_joliet:
            walk_key = 'joliet_path'
            walker = self._pycdlib_instance.walk(joliet_path='/')
        elif self._pycdlib_instance.has_rock_ridge():
            walk_key = 'rr_path'
            walker = self._pycdlib_instance.walk(rr_path='/')
        else:
            walk_key = 'iso_path'
            walker = self._pycdlib_instance.walk(iso_path='/')

        for root, dirs, files in walker:
            parent_node = node_map.get(root)
            if not parent_node:
                logger.warning(f"Could not find parent node for path: {root}")
                continue

            for item_name in dirs + files:
                is_directory = item_name in dirs
                item_path = posixpath.join(root, item_name)

                try:
                    record = self._pycdlib_instance.get_record(**{walk_key: item_path})
                    if not record:
                        logger.warning(f"Could not retrieve record for path: {item_path}")
                        continue
                except Exception as e:
                    logger.error(f"Error retrieving record for {item_path}: {e}")
                    continue

                is_hidden = False
                if walk_key != 'udf_path':
                    is_hidden = (record.file_flags & 1) != 0

                data_length = 0
                if walk_key == 'udf_path':
                    data_length = record.get_data_length()
                else:
                    data_length = record.data_length

                date_obj = None
                if walk_key == 'udf_path':
                    date_obj = record.mod_time
                else:
                    date_obj = record.date

                new_node = {
                    'name': item_name,
                    'is_directory': is_directory,
                    'is_hidden': is_hidden,
                    'size': data_length,
                    'date': self._format_pycdlib_date(date_obj),
                    'children': [],
                    'parent': parent_node,
                    'iso_path': item_path,
                    'is_new': False
                }
                parent_node['children'].append(new_node)

                if is_directory:
                    node_map[item_path] = new_node
        return root_node

    def _format_pycdlib_date(self, pycdlib_date):
        """Formats a pycdlib date dictionary into a string."""
        try:
            return (f"{pycdlib_date['year']:04d}-{pycdlib_date['month']:02d}-{pycdlib_date['day']:02d} "
                    f"{pycdlib_date['hour']:02d}:{pycdlib_date['minute']:02d}:{pycdlib_date['second']:02d}")
        except (TypeError, KeyError):
            return "Unknown"

    def save_iso(self, output_path, use_joliet, use_rock_ridge, progress_callback=None, make_hybrid=False, use_udf=True):
        """
        Saves the current in-memory ISO structure to a new file.

        Args:
            output_path (str): The path to save the new ISO file to.
            use_joliet (bool): Whether to use Joliet extensions for long filenames.
            use_rock_ridge (bool): Whether to use Rock Ridge extensions.
            progress_callback (function): A callback for progress updates.
            make_hybrid (bool): Whether to make the ISO a hybrid ISO.
            use_udf (bool): Whether to use UDF.
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
                core=self,
                progress_callback=progress_callback,
                make_hybrid=make_hybrid,
                use_udf=use_udf
            )
            builder.build()
            self.current_iso_path = output_path
            self.iso_modified = False
        except Exception as e:
            logger.exception(f"Failed to save ISO to {output_path}: {e}")
            raise

    def get_file_data(self, node):
        """
        Retrieves the data for a given file node.

        Args:
            node (dict): The file node to retrieve data for.

        Returns:
            bytes: The file data.
        """
        if node.get('is_new'):
            return node.get('file_data', b'')

        if node.get('is_cue_track'):
            bin_path = node['cue_bin_file']
            offset = node['cue_offset']
            size = node['size']
            if os.path.exists(bin_path):
                try:
                    with open(bin_path, 'rb') as f:
                        f.seek(offset)
                        return f.read(size)
                except (IOError, OSError) as e:
                    logger.error(f"Error reading BIN file '{bin_path}': {e}")
                    return b''
            else:
                logger.error(f"BIN file not found: {bin_path}")
                return b''

        if not self._pycdlib_instance:
            logger.warning("get_file_data called for ISO node but no pycdlib instance is available.")
            return b''

        if self._pycdlib_instance.has_udf():
            iso_path_key = 'udf_path'
        elif self.is_joliet:
            iso_path_key = 'joliet_path'
        elif self._pycdlib_instance.has_rock_ridge():
            iso_path_key = 'rr_path'
        else:
            iso_path_key = 'iso_path'

        try:
            with self._pycdlib_instance.open_file_from_iso(**{iso_path_key: node['iso_path']}) as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error getting file data for {node.get('name')} using pycdlib: {e}")
            return b''

    def add_file_to_directory(self, file_path, target_node):
        """
        Adds a file from the local filesystem to a directory in the ISO structure.

        Args:
            file_path (str): The path to the local file to add.
            target_node (dict): The target directory node in the ISO tree.
        """
        if not target_node['is_directory']:
            target_node = target_node['parent']

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

        if any(c['name'].lower() == folder_name.lower() and c['is_directory'] for c in target_node['children']):
            logger.warning(f"Folder '{folder_name}' already exists in '{self.get_node_path(target_node)}'")
            return

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
        try:
            parent = node_to_remove.get('parent')
            if parent and 'children' in parent:
                node_name = node_to_remove.get('name', 'Unnamed')
                parent_path = self.get_node_path(parent)
                logger.info(f"Removing node '{node_name}' from '{parent_path}'")
                original_len = len(parent['children'])
                parent['children'] = [c for c in parent['children'] if id(c) != id(node_to_remove)]

                if len(parent['children']) < original_len:
                    self.iso_modified = True
                    logger.info(f"Successfully removed node '{node_name}'.")
                else:
                    logger.warning(f"Node '{node_name}' not found in parent '{parent_path}' for removal.")
            elif not parent:
                logger.error("Cannot remove node: node has no parent.")
            else: # parent exists but has no 'children' key
                logger.error("Cannot remove node: parent is malformed and has no 'children' list.")
        except Exception as e:
            logger.exception(f"An unexpected error occurred while removing a node: {e}")
            # Depending on desired robustness, you might want to re-raise or handle differently
            raise

    def get_node_path(self, node):
        """
        Gets the full path string for a given node in the directory tree.

        Args:
            node (dict): The node to get the path for.

        Returns:
            str: The full path of the node.
        """
        if not node or not node.get('parent') or node.get('parent') is node:
            return '/'
        path_parts = []
        current = node
        while current and current.get('parent') and current.get('parent') is not current:
            path_parts.append(current['name'])
            current = current['parent']
        return '/' + '/'.join(reversed(path_parts)).replace('//', '/')

    def find_non_compliant_filenames(self):
        """
        Scans the directory tree for filenames that do not comply with the
        strict ISO9660 Level 1 standard.

        Returns:
            list: A list of non-compliant filenames.
        """
        non_compliant_files = []
        iso9660_pattern = re.compile(r'^[A-Z0-9_]+$')

        def check_node(node):
            if node['name'] != '/':
                if node['name'].count('.') > 1:
                    non_compliant_files.append(node['name'])

                base, ext = os.path.splitext(node['name'])
                if ext: ext = ext[1:]

                if not iso9660_pattern.match(base.upper()) or \
                   (ext and not iso9660_pattern.match(ext.upper())):
                    non_compliant_files.append(node['name'])

            for child in node.get('children', []):
                check_node(child)

        if self.directory_tree:
            check_node(self.directory_tree)

        return list(set(non_compliant_files))

    def _extract_boot_info(self):
        """
        Extracts boot information from the loaded ISO and populates
        the self.extracted_boot_info list.
        """
        self.extracted_boot_info = []
        logger.debug("Attempting to extract boot info from loaded ISO.")

        if not hasattr(self._pycdlib_instance, 'eltorito_boot_catalog'):
            logger.debug("No El Torito boot catalog found in the ISO.")
            return

        try:
            catalog = getattr(self._pycdlib_instance, 'eltorito_boot_catalog', None)
            if not catalog:
                logger.warning("pycdlib has El Torito but no catalog object found.")
                return

            entries_to_process = []
            if hasattr(catalog, 'initial_entry'):
                initial_entry = getattr(catalog, 'initial_entry')
                # Check if the entry is actually initialized with data
                if initial_entry and getattr(initial_entry, '_initialized', False):
                    entries_to_process.append(initial_entry)

            # In case of multi-boot, there might be a list. Let's check common names.
            for attr_name in ['boot_entries', 'entries']:
                if hasattr(catalog, attr_name):
                    entries_to_process.extend(getattr(catalog, attr_name, []))

            # Remove duplicates, as initial_entry might also be in a list
            if entries_to_process:
                entries_to_process = list(dict.fromkeys(entries_to_process))

            logger.debug(f"Found {len(entries_to_process)} boot entries to process.")

            for entry in entries_to_process:
                media_type = getattr(entry, 'boot_media_type', -1)

                # Map all floppy types to the generic 'floppy' string for consistency with the GUI.
                media_map = {0: 'noemul', 1: 'floppy', 2: 'floppy', 3: 'floppy', 4: 'hdemul'}
                emulation_type = media_map.get(media_type, 'unknown')

                boot_inode_num = getattr(entry, 'inode', -1)
                boot_image_path = "Unknown"
                if boot_inode_num != -1:
                    for root, _, files in self._pycdlib_instance.walk(iso_path='/'):
                        for f in files:
                            try:
                                record = self._pycdlib_instance.get_record(iso_path=posixpath.join(root, f))
                                if record.inode == boot_inode_num:
                                    boot_image_path = posixpath.join(root, f)
                                    break
                            except (pycdlib.pycdlibexception.PyCdlibException, AttributeError, KeyError) as e:
                                logger.debug(f"Could not retrieve record for {posixpath.join(root, f)}: {e}")
                                continue
                        if boot_image_path != "Unknown":
                            break

                info = {
                    'platform_id': getattr(entry, 'system_type', -1),
                    'emulation_type': emulation_type,
                    'boot_image_path': boot_image_path,
                    'load_segment': getattr(entry, 'load_segment', -1),
                }
                self.extracted_boot_info.append(info)
                logger.debug(f"Extracted boot entry: {info}")

        except Exception as e:
            logger.error(f"An unexpected error occurred during boot info extraction: {e}")

class ISOBuilder:
    """
    Builds an ISO 9660 file from an in-memory directory tree using pycdlib.
    """
    def __init__(self, root_node, output_path, volume_id="TK_ISO_VOL",
                 use_joliet=True, use_rock_ridge=True,
                 boot_image_path=None, efi_boot_image_path=None,
                 boot_emulation_type='noemul', core=None, progress_callback=None, make_hybrid=False, use_udf=True):
        self.root_node = root_node
        self.output_path = output_path
        self.volume_id = volume_id
        self.use_joliet = use_joliet
        self.use_rock_ridge = use_rock_ridge
        self.boot_image_path = boot_image_path
        self.efi_boot_image_path = efi_boot_image_path
        self.boot_emulation_type = boot_emulation_type
        self.core = core
        self.progress_callback = progress_callback
        self.make_hybrid = make_hybrid
        self.use_udf = use_udf
        self.iso = pycdlib.PyCdlib()

    def build(self):
        """
        Builds the ISO file and writes it to the output path.
        """
        logger.info("Starting ISO build process with pycdlib.")

        udf_version = '2.60' if self.use_udf else None
        try:
            self.iso.new(
                interchange_level=3,
                vol_ident=self.volume_id,
                joliet=3 if self.use_joliet else None,
                rock_ridge='1.09' if self.use_rock_ridge else None,
                udf=udf_version
            )
        except Exception as e:
            logger.exception(f"Failed to initialize new ISO with pycdlib: {e}")
            raise

        all_nodes = self._get_all_nodes_flat(self.root_node, '/', '/', '/')
        all_nodes.sort(key=lambda x: x[0].count('/'))

        for joliet_path, iso9660_path, udf_path, node in all_nodes:
            rr_name = node['name']

            # Don't use Joliet path if the name is too long.
            # UDF and Rock Ridge can handle it.
            current_joliet_path = joliet_path
            if len(node['name']) > 64:
                current_joliet_path = None

            if node['is_directory']:
                try:
                    self.iso.add_directory(iso9660_path, rr_name=rr_name, joliet_path=current_joliet_path, udf_path=udf_path)
                except Exception as e:
                    if 'File already exists' not in str(e):
                        logger.error(f"Failed to add directory {joliet_path} to ISO: {e}")
                        raise
            else:
                try:
                    file_data = self.core.get_file_data(node)
                    self.iso.add_fp(BytesIO(file_data), len(file_data), iso9660_path, rr_name=rr_name, joliet_path=current_joliet_path, udf_path=udf_path)
                except Exception as e:
                    logger.error(f"Failed to add file {joliet_path} to ISO: {e}")
                    raise

        if self.boot_image_path or self.efi_boot_image_path:
            self._add_boot_images()
            if self.make_hybrid:
                self.iso.add_isohybrid()

        self.iso.write(self.output_path, progress_cb=self.progress_callback)
        self.iso.close()
        logger.info(f"ISO build process completed successfully. Output at: {self.output_path}")

    def _sanitize_iso9660_name(self, name):
        """
        Sanitizes a filename to be compliant with the basic ISO9660 standard.
        """
        base, ext = os.path.splitext(name)
        sanitized_base = re.sub(r'[^A-Z0-9_]', '_', base.upper())
        if not sanitized_base: sanitized_base = '_'
        if ext:
            sanitized_ext = re.sub(r'[^A-Z0-9_]', '_', ext[1:].upper())
            return f"{sanitized_base[:8]}.{sanitized_ext[:3]}"
        return sanitized_base[:8]

    def _get_all_nodes_flat(self, node, joliet_path, iso9660_path, udf_path):
        """
        Walks the directory tree and returns a flat list of all nodes
        with their full Joliet, ISO9660, and UDF paths.
        """
        nodes = []
        for child in node['children']:
            child_joliet_path = posixpath.join(joliet_path, child['name'])
            child_udf_path = posixpath.join(udf_path, child['name'])
            sanitized_name = self._sanitize_iso9660_name(child['name'])
            child_iso9660_path = posixpath.join(iso9660_path, sanitized_name)

            nodes.append((child_joliet_path, child_iso9660_path, child_udf_path, child))
            if child['is_directory']:
                nodes.extend(self._get_all_nodes_flat(child, child_joliet_path, child_iso9660_path, child_udf_path))
        return nodes

    def _add_boot_images(self):
        """Adds boot images to the ISO if they exist."""
        logger.info("Adding boot images to the ISO.")
        try:
            self.iso.add_directory('/BOOT', rr_name='BOOT', joliet_path='/boot')
        except pycdlib.pycdlibexception.PyCdlibInvalidInput as e:
            if 'File already exists' not in str(e): raise

        if self.boot_image_path and os.path.exists(self.boot_image_path):
            bios_boot_filename = os.path.basename(self.boot_image_path)
            bios_iso_path = f'/BOOT/{self._sanitize_iso9660_name(bios_boot_filename)}'
            joliet_bios_iso_path = f'/boot/{bios_boot_filename}'
            self.iso.add_file(self.boot_image_path, bios_iso_path, rr_name=bios_boot_filename, joliet_path=joliet_bios_iso_path)
            self.iso.add_eltorito(bios_iso_path, media_name=self.boot_emulation_type)

        if self.efi_boot_image_path and os.path.exists(self.efi_boot_image_path):
            efi_boot_filename = os.path.basename(self.efi_boot_image_path)
            efi_iso_path = f'/BOOT/{self._sanitize_iso9660_name(efi_boot_filename)}'
            joliet_efi_iso_path = f'/boot/{efi_boot_filename}'
            self.iso.add_file(self.efi_boot_image_path, efi_iso_path, rr_name=efi_boot_filename, joliet_path=joliet_efi_iso_path)
            self.iso.add_eltorito(efi_iso_path, efi=True)
