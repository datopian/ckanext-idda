import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import Blueprint, render_template
import logging
from ckan.lib.plugins import DefaultTranslation
import json
import ckan.authz as authz

from ckanext.pages import db
from ckanext.pages.actions import HTMLFirstImage
import ckan.lib.dictization.model_dictize as model_dictize


log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
def hello_plugin():
    return u'Hello from the Datopian Theme extension'


class IddaPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IActions)


    def get_actions(self):
        return {
            'package_search': package_search,
            'package_show': package_show,
            'package_create': package_create,
            'package_update': package_update,
            'organization_create': organization_create,
            'group_create': group_create,
            'organization_update': organization_update,
            'group_update': group_update,
            "idda_pages_list": pages_list,
            "idda_showcase_list": showcase_list,
        }

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets',
                             'idda')
        

    # IBlueprint

    def get_blueprint(self):
        u'''Return a Flask Blueprint object to be registered by the app.'''
        # Create Blueprint for plugin
        blueprint = Blueprint(self.name, self.__module__)
        blueprint.template_folder = u'templates'
        # Add plugin url rules to Blueprint object
        blueprint.add_url_rule('/hello_plugin', '/hello_plugin', hello_plugin)
        return blueprint


@plugins.toolkit.chained_action
@toolkit.side_effect_free
def package_search(original_action, context, data_dict):

    result = original_action(context, data_dict)
    for pkg in result.get('results', None):
        try:
            if not pkg.get('notes', None):
                note = pkg.get('notes_translated', None)
                if note:
                    pkg["notes"] = note.get('az', "")
            pkg["total_downloads"] = toolkit.get_action('package_stats')(context, {'package_id': pkg['id']})
        except:
            pkg["total_downloads"] = 0

    return result


@plugins.toolkit.chained_action
@toolkit.side_effect_free
def package_show(original_action, context, data_dict):
    result = original_action(context, data_dict)
    id = result.get('id')
    try:
        result["total_downloads"] = toolkit.get_action('package_stats')(context, {'package_id': result['id']})
    except:
        result["total_downloads"] = 0

    return result


@plugins.toolkit.chained_action
def package_create(original_action, context, data_dict):
    data_dict["notes"] = data_dict.get('notes_translated-az', '')
    result = original_action(context, data_dict)
    return result

@plugins.toolkit.chained_action
def package_update(original_action, context, data_dict):
    data_dict["notes"] = data_dict.get('notes_translated-az', '')
    result = original_action(context, data_dict)
    return result


@plugins.toolkit.chained_action                                                                                                                                                    
def organization_create(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-az', '') 

    if data_dict.get('notes_translated-az'):                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-az', '')  
                                                     
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@plugins.toolkit.chained_action                                                                                                                                                    
def group_create(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-az', '') 

    if data_dict['description_translated-az']:                                                                                                                         
        data_dict['description'] = data_dict.get('description_translated-az', '')  
    
                                                               
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result


@plugins.toolkit.chained_action                                                                                                                                                    
def organization_update(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-az', '') 

    if data_dict.get('notes_translated-az'):                                                                                                                         
        data_dict['description'] = data_dict.get('notes_translated-az', '')  
                                                     
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result

@plugins.toolkit.chained_action                                                                                                                                                    
def group_update(up_func,context,data_dict): 
    data_dict['title'] = data_dict.get('title_translated-az', '') 

    if data_dict['description_translated-az']:                                                                                                                         
        data_dict['description'] = data_dict.get('description_translated-az', '')  
    
                                                               
    result = up_func(context, data_dict)                                                                                                                                                                                                                                                                                                     
    return result


@plugins.toolkit.side_effect_free
def pages_list(context, data_dict):
    try:
        plugins.toolkit.check_access('ckanext_pages_list', context, data_dict)
    except p.toolkit.NotAuthorized:
        plugins.toolkit.abort(401, plugins.toolkit._('Not authorized to see this page'))
    search = {}
    org_id = data_dict.get('org_id')
    ordered = data_dict.get('order')
    order_publish_date = data_dict.get('order_publish_date')
    page_type = data_dict.get('page_type')
    private = data_dict.get('private', True)
    if ordered:
        search['order'] = True
    if page_type:
        search['page_type'] = page_type
    if order_publish_date:
        search['order_publish_date'] = True

    if not org_id:
        search['group_id'] = None
        try:
            plugins.toolkit.check_access('ckanext_pages_update', context, data_dict)
            if not private:
                search['private'] = False
        except plugins.toolkit.NotAuthorized:
            search['private'] = False
    else:
        group = context['model'].Group.get(org_id)
        user = context['user']
        member = authz.has_user_permission_for_group_or_org(group.id, user, 'read')
        search['group_id'] = org_id
        if not member:
            search['private'] = False

    # fetch all pages
    pages = db.Page.pages(**search)

    # helper to extract locale and base title
    def split_locale(name):
        if name.startswith('en-'):
            return 'en', name[3:]
        elif name.startswith('ru-'):
            return 'ru', name[3:]
        else:
            return 'az', name

    # group pages by base_title
    grouped = {}
    for pg in pages:
        locale, base = split_locale(pg.name)
        # build the base dict if missing
        if base not in grouped:
            grouped[base] = {}
        # serialize page
        parser = HTMLFirstImage()
        parser.feed(pg.content)
        pg_row = {
            'title': pg.title,
            'content': pg.content,
            'name': pg.name,
            'publish_date': pg.publish_date.isoformat() if pg.publish_date else None,
            'group_id': pg.group_id,
            'page_type': pg.page_type,
        }
        if parser.first_image:
            pg_row['image'] = parser.first_image
        if pg.extras:
            pg_row.update(json.loads(pg.extras))
        # store under its locale
        grouped[base][locale] = pg_row

    # build final list: one per base
    out_list = []
    for base, locales in grouped.items():
        # choose the default AZ row as the top-level entry if available,
        # otherwise pick any locale arbitrarily
        top = locales.get('az') or next(iter(locales.values()))
        entry = top.copy()
        # attach other locales (excluding the one used as top)
        entry['translates_pages'] = {
            loc: data for loc, data in locales.items()
            if data['name'] != top['name']
        }
        out_list.append(entry)

    return out_list


@plugins.toolkit.side_effect_free
def showcase_list(context, data_dict):
    '''Return a list of all showcases in the site, grouping translations under `translated_showcase`.'''

    # Check user permissions
    toolkit.check_access('ckanext_showcase_list', context, data_dict)

    model = context["model"]

    # Query all active showcases
    q = model.Session.query(model.Package) \
        .filter(model.Package.type == 'showcase') \
        .filter(model.Package.state == 'active')

    # Convert to dictionaries
    packages = [model_dictize.package_dictize(pkg, context) for pkg in q.all()]

    # Separate base showcases and translations
    base_map = {}
    translations = []
    for pkg in packages:
        name = pkg.get('name', '')
        # Identify translations by a single dash separating locale and base name
        if '-' in name:
            locale, base_name = name.split('-', 1)
            # simple locale code check (e.g., 'en', 'ru')
            if locale.isalpha() and len(locale) == 2:
                translations.append((locale, base_name, pkg))
                continue
        # Otherwise treat as base showcase
        pkg['translated_showcase'] = {}
        base_map[name] = pkg

    # Attach translations to their base entries
    for locale, base_name, trans_pkg in translations:
        base_entry = base_map.get(base_name)
        if base_entry:
            base_entry['translated_showcase'][locale] = trans_pkg
        else:
            # If no base found, you can decide to include or log
            # For now, skip unmatched translations
            continue

    # Return only base showcases with their translations
    return list(base_map.values())
