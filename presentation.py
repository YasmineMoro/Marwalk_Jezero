"""English presentation of legacy application labels; user note text is preserved."""
import re

def mission_name(value):
    if value in ('Delta de Jezero · mission Amalik','Delta occidental — EVA simulée'):
        return 'Jezero Delta · Amalik mission' if 'Amalik' in value else 'Western delta — simulated EVA'
    if re.fullmatch(r'Démo .+ — Amalik',value or ''):
        return 'MarsWalk team demonstration — Amalik'
    if value=='Démo reproductible — delta occidental':return 'Reproducible demonstration — western delta'
    return value

def phase_name(value):
    return {'marche':'walking','terminée':'completed'}.get(value,value)

def present_document(body):
    body['mission']['name']=mission_name(body['mission']['name'])
    for route in [body.get('route'),*body.get('route_history',[])]:
        if route and route.get('parameters'):route['parameters']['name']=mission_name(route['parameters']['name'])
    if body.get('progress'):body['progress']['phase']=phase_name(body['progress']['phase'])
    for note in body.get('observations',[]):
        note['category']={'géologie':'geology','photographie':'photography','échantillonnage fictif':'simulated sampling','autre':'other'}.get(note.get('category'),note.get('category'))
        if note.get('status')=='observé (simulation)':note['status']='observed (simulation)'
    return body
