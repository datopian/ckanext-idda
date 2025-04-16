import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from flask import Blueprint, render_template
import logging

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
            'package_update': package_update
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