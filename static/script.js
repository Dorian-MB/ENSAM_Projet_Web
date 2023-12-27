	
    

function handleOptionClick(checkbox) {
    var checkboxes = document.querySelectorAll('.menuDeroulant .option');
    if (checkbox.id === 'aucuneOption') {
        // Si "Aucune Option" est cochée, désélectionner toutes les autres
        checkboxes.forEach(function (checkbox) {
            checkbox.checked = false;
        });
    } else {
        // Si une autre option est cochée, désélectionner "Aucune Option"
        document.getElementById('aucuneOption').checked = false;
    }
}


function showInputs() {
    var searchType = document.getElementById("searchType").value;
    var inputContainer = document.getElementById("input_client_suivit_commande");

    // Vider le conteneur avant d'ajouter des inputs spécifiques
    inputContainer.innerHTML = '';
    if (searchType === "commande") {
        inputContainer.innerHTML = '<input type="text" name="id_commande" placeholder="Entrez le numéro de commande" required/>';
    } else if (searchType === "nom_prenom") {
        inputContainer.innerHTML = '<input type="text" name="nom" placeholder="Entrez votre nom" required/>' + '<br>' +
                                   '<input type="text" name="prenom" placeholder="Entrez votre prénom" required/>';
    }
}


function confirmSubmission() {
    // Utilisez window.confirm pour demander une confirmation à l'utilisateur
    if (window.confirm("Voulez-vous vraiment envoyer ce formulaire ?")) {
        // Si l'utilisateur confirme, le formulaire sera soumis
        document.getElementById("confimer_suppression").submit();
    } else {
        // Si l'utilisateur ne confirme pas, on ne fait rien
        alert("Envoi annulé.");
    }
}