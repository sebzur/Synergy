<script>  
    $(document).ready(function() {
	$('{{ selector }}').dataTable({ "bFilter": {{ is_filtered|yesno:"true,false"}},
					"bPaginate": {{ is_paginated|yesno:"true,false"}},
					{% if page_rows %}"iDisplayLength": {{ page_rows }},{% endif %}
					{% if transfile %}"oLanguage": {"sUrl": "{{ transfile }}"},{% endif %}
                                 	"bJQueryUI": true {# IMPORTANT: keep no semicolon at the end here #}
				      });
    });
</script>
