<script>  
    $(document).ready(function() {
	$('{{ selector }}').dataTable({"iDisplayLength": 100,
				       "bJQueryUI": true,
				       "oLanguage": {
					   "sUrl": "/static/datatables/language/pl_PL.txt"
				       }
				      });
    } );
</script>
