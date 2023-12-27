**TODO :**

- General :
  - ajouter les 'action' dans les fichiers html : `<form method='post' action='{{ url_for(" nom fct py ") }}'>`
    (pas obligatoire ca marche quand meme sans)
    - Verifier si on peut split des fonctions en deux avec l'ajoue du 'action'
  - verifier attendu prof (agilog/agigreen)
  - modifier page stock en "definir les stock initiaux" (ou du genre)
  - implementer un timer visible partout (je crois c'est attendu)    

- client : 
  - debug `confirmSubmission` dans scrip.js, actuellement formulaire s'envoi quand meme
    (le formulaire s'envoi quand meme peux etre a cause du `action` dans le formulaire html, mais pas sur)

- agilog :
  - page cmd_agilean : faire page des kits ?
    pb avec la bbd pas de table de kit (site 219 ont les kit)
    table bdd : (id_kit, id_piece, quantiter)

- bonus :
  - date chq envoie/reception => faire une page avec tout les recapitulatifs ?
  ```
  agilean:
  date_commande_client, date_envoie_agilog, date_reception_agilog, date_expedition_client, date_livraison_client

  agilog : 
  date_envoi_agigreen, date_reception_agigreen, date_expedition_agilean

  agigreen:
  date_expedition_agilog
  ```