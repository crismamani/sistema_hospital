// static/js/cie_buscador.js
function inicializarBuscadorCIE() {
    $('.cie-buscador').select2({
        ajax: {
            url: "/hospital/buscar-cie10/", // Usa la URL directa si el tag de django falla en JS externo
            dataType: 'json',
            delay: 150,
            data: function (params) {
                return { q: params.term };
            },
            processResults: function (data) {
                return { results: data.results };
            },
            cache: true
        },
        minimumInputLength: 1,
        placeholder: "Cód...",
        allowClear: true,
        width: '100%'
    });

    // Esta parte es la que llena la descripción automáticamente en cualquier formulario
    $('.cie-buscador').on('select2:select', function (e) {
        var data = e.params.data;
        var partes = data.text.split(' - ');
        var descripcionJusta = partes.slice(1).join(' - ');
        
        // Buscamos el input de descripción en la misma fila (diag-row o similar)
        $(this).closest('.diag-row, .diag-row-ingreso').find('.diag-inp, .desc-resultado').val(descripcionJusta);
    });

    // Forzar foco para que deje escribir
    $(document).on('select2:open', function(e) {
        document.querySelector('.select2-search__field').focus();
    });
}

$(document).ready(function() {
    inicializarBuscadorCIE();
});