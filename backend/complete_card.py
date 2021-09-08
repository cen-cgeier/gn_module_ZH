from datetime import datetime

from sqlalchemy.sql.expression import true

import pdb

from .models import *


def get_complete_card(full_zh):
    complete_card = {}

    identification = {
        "Nom usuel de la zone humide": full_zh.properties['main_name'],
        "Autre nom": full_zh.properties['secondary_name'],
        "Partie d'un ensemble": get_bool(full_zh.properties['is_id_site_space']),
        **({"Nom du grand ensemble": TZH.get_site_space_name(full_zh.properties['id_site_space'])} if full_zh.properties['is_id_site_space'] else {}),
        "Code de la zone humide": full_zh.properties['code']
    }

    localisation = {
        "Région": full_zh.properties['geo_info']['regions'],
        "Département": full_zh.properties['geo_info']['departments'],
        "Commune": get_communes_info(full_zh.properties['id_zh'])
    }

    auteur = {
        "Auteur de la fiche": get_author(full_zh.properties['id_zh']),
        "Auteur des dernières modifications": get_author(full_zh.properties['id_zh'], type='co-author'),
        "Date d'établissement": datetime.strptime(full_zh.properties['create_date'], '%Y-%m-%d %H:%M:%S').date().strftime("%d/%m/%Y"),
        "Date des dernières modifications": datetime.strptime(full_zh.properties['update_date'], '%Y-%m-%d %H:%M:%S.%f').date().strftime("%d/%m/%Y")
    }

    references = get_references(full_zh.properties['id_references'])

    complete_card.update({
        "1- Renseignements généraux": {
            "1.1- Identification de la zone humide": {
                "Identification": identification,
                "Localisation de la zone humide": localisation
            },
            "1.2- Auteur": auteur,
            "1.4- Principales références bibliographiques": references
        },
        "2- Délimitation de la zone humide et de l'espace de fonctionnalité": {
            "2.1- Critères de délimitation de la zone humide": {
                "Critères utilisés": get_mnemo(full_zh.properties['id_lims']),
                "Remarque": full_zh.properties['remark_lim']
            },
            "2.2- Critère de délimitation de l'espace de fonctionnalité": {
                "Critères utilisés": get_mnemo(full_zh.properties['id_lims_fs']),
                "Remarque": full_zh.properties['remark_lim_fs']
            }
        },
        "3- Description du bassin versant et de la zone humide": {
            "3.2- Présentation de la zone humide et de ses milieux": {
                "Typologie SDAGE": get_mnemo(full_zh.properties['id_sdage']),
                "Typologie locale": get_mnemo(full_zh.properties['id_sage']),
                "Corine Biotope": get_cb(full_zh.properties['cb_codes_corine_biotope']),
                "Remarques": full_zh.properties['remark_pres']
            },
            "3.3- Description de l'espace de fonctionnalité": {
                "Occupation des sols": get_mnemo(full_zh.properties['id_corine_landcovers'])
            },
            "3.4- Usage et processus naturels": {
                "Activités": get_activities(full_zh.properties['activities']),
                "Evaluation globale des menaces potentielles ou avérées": get_mnemo(full_zh.properties['id_thread']),
                "Remarques": full_zh.properties['global_remark_activity']
            }
        },
        "4- Fonctionnement de la zone humide": {
            "4.1- Régime hydrique": {
                "Entrée d'eau": get_flows(full_zh.properties['flows'], type="inflows"),
                "Sortie d'eau": get_flows(full_zh.properties['flows'], type="outflows"),
                "Submersion fréquence": get_mnemo(full_zh.properties['id_frequency']),
                "Submersion étendue": get_mnemo(full_zh.properties['id_spread']),
            },
            "4.2- Connexion de la zone humide dans son environnement": get_mnemo(full_zh.properties['id_connexion']),
            "4.3- Diagnostic fonctionnel": {
                "Fonctionnalité hydrologique / biogéochimique": get_mnemo(full_zh.properties['id_diag_hydro']),
                "Fonctionnalité biologique / écologique": get_mnemo(full_zh.properties['id_diag_bio']),
                "Commentaires": full_zh.properties['remark_diag']
            }
        },
        "5- Fonctions écologiques, valeurs socio-écologiques, intérêt patrimonial": {
            "5.1- Fonctions hydrologiques / biogéochimiques": get_function_info(full_zh.properties['fonctions_hydro'], type="fonctions_hydro"),
            "5.2- Fonctions biologiques / écologiques": get_function_info(full_zh.properties['fonctions_bio'], type="fonctions_bio"),
            "5.4- Intérêt patrimonial": get_function_info(full_zh.properties['interet_patrim'], type="interet_patrim"),
            "5.4.1- Habitats naturels humides patrimoniaux": {
                "Cartographie d'habitats": get_bool(full_zh.properties['is_carto_hab']),
                "Nombre d'habitats": get_int(full_zh.properties['nb_hab']),
                "Recouvrement total de la ZH (%)": "Non évalué" if full_zh.properties['total_hab_cover'] == "999" else full_zh.properties['total_hab_cover'],
                "Habitats naturels patrimoniaux": get_hab_heritages(full_zh.properties['hab_heritages'])
            },
            "5.4.2- Faune et flore patrimoniale": {
                "Flore - nombre d'espèces": get_int(full_zh.properties['nb_flora_sp']),
                "Faune - nombre d'espèces de vertébrés": get_int(full_zh.properties['nb_vertebrate_sp']),
                "Faune - nombre d'espèces d'invertébrés": get_int(full_zh.properties['nb_invertebrate_sp'])
            },
            "5.3- Valeurs socio-économiques": get_function_info(full_zh.properties['val_soc_eco'], type="val_soc_eco")
        }

    })
    return complete_card


def get_bool(bool):
    if bool:
        return 'Oui'
    return 'Non'


def get_communes(communes):
    commune_insee = [k for k, v in [(k, v)
                                    for x in communes for (k, v) in x.items()]]
    commune_names = [v for k, v in [(k, v)
                                    for x in communes for (k, v) in x.items()]]
    return {
        "communes": commune_names,
        "code_insee": commune_insee
    }


def get_communes_info(id_zh):
    q = CorZhArea.get_municipalities_info(id_zh)
    communes = [{
        "Commune": commune.LiMunicipalities.nom_com,
        "Code INSEE": commune.LiMunicipalities.insee_com,
        "Couverture ZH par rapport à la surface de la commune": str(commune.CorZhArea.cover) if commune.CorZhArea.cover is not None else 'Non renseigné'
    } for commune in q]
    return communes


def get_author(id_zh, type='author'):
    if type == 'author':
        prenom = DB.session.query(TZH).filter(
            TZH.id_zh == id_zh).one().authors.prenom_role
        nom = DB.session.query(TZH).filter(
            TZH.id_zh == id_zh).one().authors.nom_role
    else:
        prenom = DB.session.query(TZH).filter(
            TZH.id_zh == id_zh).one().coauthors.prenom_role
        nom = DB.session.query(TZH).filter(
            TZH.id_zh == id_zh).one().coauthors.nom_role
    return prenom + ' ' + nom.upper()


def get_references(ref_list):
    if ref_list:
        return [
            {
                "Titre du document": ref['title'],
                "Auteurs": ref['authors'],
                "Année de parution": ref['pub_year'],
                "Bassins versants": 'en attente',
                "Editeur": ref['editor'],
                "Lieu": ref['editor_location']
            }
            for ref in ref_list
        ]
    return "Non renseigné"


def get_mnemo(ids):
    if ids:
        if type(ids) is int:
            return DB.session.query(TNomenclatures).filter(TNomenclatures.id_nomenclature == ids).one().mnemonique
        return [DB.session.query(TNomenclatures).filter(TNomenclatures.id_nomenclature == id).one().mnemonique for id in ids]
    return "Non renseigné"


def get_activities(activities):
    if activities:
        return [
            {
                "Activité humaine": get_mnemo(activity['id_human_activity']),
                "Localisation": get_mnemo(activity['id_localisation']),
                "Impacts": get_mnemo(activity['ids_impact']),
                "Remarques": activity['remark_activity']
            }
            for activity in activities
        ]
    return "Non renseigné"


def get_cb(cb_ids):
    if cb_ids:
        cbs = BibCb.get_label()
        cbs_info = {}
        for cb in cbs:
            if cb.BibCb.lb_code in cb_ids:
                cbs_info.update({
                    "Code Corine Biotope": cb.BibCb.lb_code,
                    "Libellé Corine Biotope": cb.Habref.lb_hab_fr,
                    "Humidité": cb.BibCb.humidity
                })
        return cbs_info
    return "Non renseigné"


def get_flows(flows, type):
    if type == "inflows":
        flow_type = "Entrée d'eau"
        id_key = "id_inflow"
        flows = flows[1]  # to do : correct json input
    else:
        flow_type = "Sortie d'eau"
        id_key = "id_outflow"
        flows = flows[0]  # to do : correct json input
    if flows[type]:
        return [
            {
                flow_type: get_mnemo(flow[id_key]),
                "Permanence": get_mnemo(flow["id_permanance"]),
                "Toponymie et compléments d'information": flow["topo"]
            }
            for flow in flows[type]
        ]
    return "Non renseigné"


def get_function_info(functions, type):
    if functions:
        return [
            {
                type: get_mnemo(function['id_function']),
                "Justification": function['justification'],
                "Qualification": get_mnemo(function['id_qualification']),
                "Connaissance": get_mnemo(function['id_knowledge'])
            }
            for function in functions
        ]
    return "Non renseigné"


def get_int(nb):
    return nb if nb is not None else 'Non évalué'


def get_hab_heritages(habs):
    if habs:
        return [
            {
                "Corine Biotope": DB.session.query(Habref).filter(Habref.cd_hab == hab['id_corine_bio']).one().lb_hab_fr,
                "Cahier Habitats": DB.session.query(Habref).filter(Habref.cd_hab == hab['id_cahier_hab']).one().lb_hab_fr,
                "Etat de préservation": get_mnemo(hab['id_preservation_state']),
                "Recouvrement de la ZH (%)": "Non évalué" if hab.hab_cover == "999" else hab.hab_cover
            }
            for hab in habs
        ]
    return "Non renseigné"
