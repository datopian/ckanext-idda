import json
import rdflib
import ckan.plugins.toolkit as tk
from rdflib.namespace import Namespace, RDF
from rdflib import URIRef, Literal
from ckanext.dcat.profiles import EuropeanDCATAP2Profile, CleanedURIRef, SchemaOrgProfile
from ckanext.dcat.utils import resource_uri
import logging

DCT = Namespace("http://purl.org/dc/terms/")
DCAT = Namespace("http://www.w3.org/ns/dcat#")
SCHEMA = Namespace("http://schema.org/")

log = logging.getLogger(__name__)

class DCTProfile(EuropeanDCATAP2Profile):
    """
    An RDF profile for the Dublin Core Terms with custom metadata mappings.
    """

    def custom_object_value(self, subject, predicate, lang="az"):
        """
        Given a subject and a predicate, returns the value of the object

        Both subject and predicate must be rdflib URIRef or BNode objects

        If found, the string representation is returned, else an empty string
        """
        
        fallback = ""
        for o in self.g.objects(subject, predicate):
            if isinstance(o, Literal):
                if o.language and o.language == lang:
                    return str(o)
                # Use first object as fallback if no object with the default language is available
                elif fallback == "":
                    fallback = str(o)
            else:
                return str(o)
        return fallback
    
    def translate(self, subject, predicate):
        data_dict = {}
        for lang in ["en", "az", "ru"]:
            value = self.custom_object_value(subject, predicate, lang)
            if value:
                data_dict[lang] = value
            else:
                data_dict[lang] = ""
        return json.dumps(data_dict)




    def parse_dataset(self, dataset_dict, dataset_ref):
        # call super method
        super(DCTProfile, self).parse_dataset(dataset_dict, dataset_ref)
        
        for field, dct_property in [
            ("title_translated", DCT.title),
            ("author_translated", DCT.creator),
            ("notes_translated", DCT.description),
            ("maintainer_translated", DCT.mediator), 
        ]:
            value = self.translate(dataset_ref, dct_property)
            if value:
                dataset_dict[field] = value



        # Resources
        for distribution in self._distributions(dataset_ref):

            for field, dct_property in [
                ("name_translated", DCT.title),
                ("notes_translated", DCT.description),
            ]:
                value = self.translate(distribution, dct_property)
                if value:
                   distribution_ref = str(distribution)
                   for resource_dict in dataset_dict.get("resources", []):
                       if resource_uri(resource_dict) == distribution_ref:
                           resource_dict[field] = value
                           break

        return dataset_dict

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        # call super method
        super(DCTProfile, self).graph_from_dataset(dataset_dict, dataset_ref)
        g = self.g

        log.info("IN DCAT_profile graph_from_dataset")
        log.info(dataset_dict)

        # Add translated fields to the graph
        for field, dct_property in [
            ("title_translated", DCT.title),
            ("author_translated", DCT.creator),
            ("notes_translated", DCT.description),
            ("maintainer_translated", DCT.mediator), 
        ]:
            if field in dataset_dict:
                for lang, value in dataset_dict[field].items():
                    g.add((dataset_ref, dct_property, Literal(value, lang=lang)))

        # Resources
        for resource_dict in dataset_dict.get("resources", []):
            distribution = CleanedURIRef(resource_uri(resource_dict))

            # Add translated fields for resources
            for field, dct_property in [
                ("name_translated", DCT.title),
                ("notes_translated", DCT.description),
            ]:
                if field in resource_dict:
                    for lang, value in resource_dict[field].items():
                        g.add((distribution, dct_property, Literal(value, lang=lang)))


class SchemaOrgMultilingualProfile(SchemaOrgProfile):
    """
    An RDF profile for Schema.org with custom metadata mappings and multilingual support.
    """

    def custom_object_value(self, subject, predicate, lang="az"):
        """
        Given a subject and a predicate, returns the value of the object

        Both subject and predicate must be rdflib URIRef or BNode objects

        If found, the string representation is returned, else an empty string
        """
        
        fallback = ""
        for o in self.g.objects(subject, predicate):
            if isinstance(o, Literal):
                if o.language and o.language == lang:
                    return str(o)
                # Use first object as fallback if no object with the default language is available
                elif fallback == "":
                    fallback = str(o)
            else:
                return str(o)
        return fallback
    
    def translate(self, subject, predicate):
        data_dict = {}
        for lang in ["en", "az", "ru"]:
            value = self.custom_object_value(subject, predicate, lang)
            if value:
                data_dict[lang] = value
            else:
                data_dict[lang] = ""
        return json.dumps(data_dict)

    def graph_from_dataset(self, dataset_dict, dataset_ref):
        super(SchemaOrgMultilingualProfile, self).graph_from_dataset(dataset_dict, dataset_ref)
        g = self.g

        log.info("IN SchemaOrgMultilingualProfile graph_from_dataset")
        log.info(dataset_dict)

        # Add translated fields to the graph
        for field, schema_property in [
            ("title_translated", SCHEMA.name),
            ("author_translated", SCHEMA.creator),
            ("notes_translated", SCHEMA.description),
            ("maintainer_translated", SCHEMA.mediator), 
        ]:
            if field in dataset_dict:
                for lang, value in dataset_dict[field].items():
                    g.add((dataset_ref, schema_property, Literal(value, lang=lang)))

        # Resources
        for resource_dict in dataset_dict.get("resources", []):
            distribution = URIRef(resource_uri(resource_dict))

            # Add translated fields for resources
            for field, schema_property in [
                ("name_translated", SCHEMA.name),
                ("notes_translated", SCHEMA.description),
            ]:
                if field in resource_dict:
                    for lang, value in resource_dict[field].items():
                        g.add((distribution, schema_property, Literal(value, lang=lang)))

    def parse_dataset(self, dataset_dict, dataset_ref):
        # call super method
        super(SchemaOrgMultilingualProfile, self).parse_dataset(dataset_dict, dataset_ref)

        for field, schema_property in [
            ("title_translated", SCHEMA.name),
            ("author_translated", SCHEMA.creator),
            ("notes_translated", SCHEMA.description),
            ("maintainer_translated", SCHEMA.mediator), 
        ]:
            value = self.translate(dataset_ref, schema_property)
            if value:
                dataset_dict[field] = value

        # Resources
        for distribution in self._distributions(dataset_ref):

            for field, schema_property in [
                ("name_translated", SCHEMA.name),
                ("notes_translated", SCHEMA.description),
            ]:
                value = self.translate(distribution, schema_property)
                if value:
                   distribution_ref = str(distribution)
                   for resource_dict in dataset_dict.get("resources", []):
                       if resource_uri(resource_dict) == distribution_ref:
                           resource_dict[field] = value
                           break

        return dataset_dict
