from core.models import Threat, SecurityFunction, RiskMatrix
from django.contrib import messages
from django.contrib.auth.models import Permission
from iam.models import Folder, RoleAssignment
from mira import settings
from django.utils.translation import gettext_lazy as _

from .validators import *

import os
import json

def get_available_library_files():
    '''
    Returns a list of available library files
    
    Returns:
        files: list of available library files
    '''
    files = []
    path = settings.BASE_DIR / 'library/libraries'
    # print absolute path
    print(os.path.abspath(path))
    for f in os.listdir(path):
        if os.path.isfile(os.path.join(path, f)) and f.endswith('.json'):
            files.append(f)
    return files

def get_available_libraries():
    '''
    Returns a list of available libraries
    
    Returns:
        libraries: list of available libraries
    '''
    files = get_available_library_files()
    path = settings.BASE_DIR / 'library/libraries'
    libraries = []
    for f in files:
        with open(path / f, 'r', encoding='utf-8') as file:
            libraries.append(json.load(file))
    libraries.sort(key=lambda x: x['locale'] + x['name'].lower())
    return libraries

def get_library_names():
    '''
    Returns a list of available library names
    
    Returns:
        names: list of available library names
    '''
    libraries = get_available_libraries()
    names = []
    for l in libraries:
        names.append(l['name'])
    return names

def get_library(name):
    '''
    Returns a library by name
    
    Args:
        name: name of the library to return
        
    Returns:
        library: library with the given name
    '''
    libraries = get_available_libraries()
    for l in libraries:
        if l['name'] == name: # TODO: use slug or cook-up some unique id instead of using 'name'
            return l
    return None

def get_library_items(library, type):
    '''
    Returns a list of items of a given type from a library
    
    Args:
        library: library to return items from
        type: type of items to return
        
    Returns:
        items: list of items of the given type from the library
    '''
    items = []
    for item in library['items']:
        if item['type'] == type:
            items.append(item)
    return items

def import_matrix(fields):
    '''
    Imports a matrix from a library
    
    Args:
        fields: matrix fields
        
    Returns:
        matrix: imported matrix
    '''
    required_fields = ['name', 'description', 'probability', 'impact', 'risk', 'grid']

    if not validate_object(required_fields, fields):
        raise Exception('Invalid matrix')

    matrix = RiskMatrix.objects.create(
        name=fields['name'],
        description=fields['description'],
        json_definition=json.dumps(fields),
        folder=Folder.get_root_folder() # TODO: make this configurable
    )

    return matrix

def import_threat(fields):
    '''
    Imports a threat from a library
    
    Args:
        fields: threat fields
        
    Returns:
        threat: imported threat
    '''
    required_fields = ['name', 'description']

    if not validate_object(required_fields, fields):
        raise Exception('Invalid threat')

    threat = Threat.objects.create(
        name=fields['name'],
        description=fields['description'],
        provider=fields['provider'],
        folder=Folder.get_root_folder() # TODO: make this configurable
    )

    return threat

def import_security_function(fields):
    '''
    Imports a security function from a library
    
    Args:
        fields: security function fields
        
    Returns:
        security_function: imported security function
    '''
    required_fields = ['name', 'description']

    if not validate_object(required_fields, fields):
        raise Exception('Invalid security function')

    security_function = SecurityFunction.objects.create(
        name=fields['name'],
        description=fields['description'],
        provider=fields['provider'],
        folder=Folder.get_root_folder() # TODO: make this configurable
    )

    return security_function

def import_matrix_view(request, fields):
    '''
    Imports a matrix from a library
    
    Args:
        fields: matrix fields
        
    Returns:
        matrix: imported matrix
    '''
    required_fields = ['name', 'description', 'probability', 'impact', 'risk', 'grid']

    if not validate_object(required_fields, fields):
        messages.error(request, _('Library was not imported: invalid matrix.'))
        raise Exception('Invalid matrix')
    
    matrix = RiskMatrix.objects.create(
        name=fields['name'],
        description=fields['description'],
        json_definition=json.dumps(fields),
        folder=Folder.get_root_folder() # TODO: make this configurable
    )

    return matrix

def import_threat_view(request, fields):
    '''
    Imports a threat from a library
    
    Args:
        fields: threat fields
        
    Returns:
        threat: imported threat
    '''
    required_fields = ['name', 'description']

    if not validate_object(required_fields, fields):
        messages.error(request, _('Library was not imported: invalid threat.'))
        raise Exception('Invalid threat')

    threat = Threat.objects.create(
        name=fields['name'],
        description=fields['description'],
        provider=fields['provider'],
        folder=Folder.get_root_folder() # TODO: make this configurable
    )

    return threat

def import_security_function_view(request, fields):
    '''
    Imports a security function from a library
    
    Args:
        fields: security function fields
        
    Returns:
        security_function: imported security function
    '''
    required_fields = ['name', 'description']

    if not validate_object(required_fields, fields):
        messages.error(request, _('Library was not imported: invalid security function.'))
        raise Exception('Invalid security function')

    security_function = SecurityFunction.objects.create(
        name=fields['name'],
        description=fields['description'],
        provider=fields['provider'],
        folder=Folder.get_root_folder() # TODO: make this configurable
    )

    return security_function

def ignore_library_object(library_objects, object_type):
    '''
    Return two lists of objects to ignore or upload

    Args:
        library_objects: objects to filter
        object_type: type of the objects
    '''
    ignored_list = []
    uploaded_list = []
    for library_objects in library_objects:
        if object_type.objects.filter(name=library_objects['name']).exists():
            ignored_list.append(library_objects)
        else:
            uploaded_list.append(library_objects)
    return uploaded_list, ignored_list


def import_library(library):
    '''
    Imports a library
    
    Args:
        library: library to import
    '''
    matrices = []
    threats = []
    security_functions = []

    for obj in library.get('objects'):
        if obj['type'] == 'matrix':
            matrices.append(obj.get('fields'))
        elif obj['type'] == 'threat':
            threats.append(obj.get('fields'))
        elif obj['type'] == 'security_function':
            security_functions.append(obj.get('fields'))
        else:
            raise Exception(_('Unknown object type: {}').format(obj["type"]))

    for matrix in matrices:
        import_matrix(matrix)

    for threat in threats:
        import_threat(threat)

    for security_function in security_functions:
        import_security_function(security_function)

    return True

def is_import_permited(request, object_type):
    '''
    Verify user permissions to import a library

    Args:
        object_type: type of the object being imported
    '''
    object_type = object_type.replace("_", "")
    if object_type == 'matrix':                 # dirty hack to avoid changing the library format
        object_type = 'riskmatrix'
    if not RoleAssignment.is_access_allowed(request.user, Permission.objects.get(codename=f"add_{object_type}"), Folder.get_root_folder()):
        messages.error(request, _("Library was not imported: permission denied for: {}").format(object_type))
        raise Exception(f"Permission denied for: {object_type}")
    return True

def import_library_view(request, library):
    '''
    Imports a library
    
    Args:
        library: library to import
    '''
    matrices = []
    threats = []
    security_functions = []
    objects_uploaded = 0
    objects_ignored = 0

    for obj in library.get('objects'):
        if obj['type'] == 'matrix' and is_import_permited(request, obj['type']):
            matrices.append(obj.get('fields'))
        elif obj['type'] == 'threat' and is_import_permited(request, obj['type']):
            threats.append(obj.get('fields'))
        elif obj['type'] == 'security_function' and is_import_permited(request, obj['type']):
            security_functions.append(obj.get('fields'))
        else:
            messages.error(request, _('Library was not imported: unknown object type: {}').format(obj['type'].replace("_", " ")))
            raise Exception(f'Unknown object type: {obj["type"]}')

    uploaded_list, ignored_list = ignore_library_object(matrices, RiskMatrix)
    objects_ignored += len(ignored_list)
    objects_uploaded += len(uploaded_list)
    for matrix in uploaded_list:
        import_matrix_view(request, matrix)

    uploaded_list, ignored_list = ignore_library_object(threats, Threat)
    objects_ignored += len(ignored_list)
    objects_uploaded += len(uploaded_list)
    for threat in uploaded_list:
        import_threat_view(request, threat)

    uploaded_list, ignored_list = ignore_library_object(security_functions, SecurityFunction)
    objects_ignored += len(ignored_list)
    objects_uploaded += len(uploaded_list)
    for security_function in uploaded_list:
        import_security_function_view(request, security_function)

    messages.success(request, _('Library "{}" imported successfully. {} object(s) imported and {} object(s) ignored.').format(library["name"], objects_uploaded, objects_ignored))
    return True