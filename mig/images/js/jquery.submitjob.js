
    // Update the runtime environment list. Show only zero install REs when it is an arc job.
    function update_runtime_env(jobtype){
        $("select[name=RUNTIMEENVIRONMENT] option").show();
        if ("arc"==jobtype){
            	$("select[name=RUNTIMEENVIRONMENT] option").filter(
                	function(){
                    		return (zeroinstall_RTE.indexOf($(this).val())==-1);
                	}
            	).hide();
        }
    }
    
    // Check if the user has a valid proxy certificate
    function validate_proxy_certificate(){
    	var settings_page = 'settings.py?output_format=json;topic=arc'; 
        $.getJSON(settings_page,{}, 
        		function(jsonRes, textStatus){
                	for(i=0; i<jsonRes.length; i++){
                		if(jsonRes[i].object_type=="warning"){
                			if (confirm("No valid ARC proxy certificate. "+jsonRes[i].text+"\n\nClick OK to open the proxy upload page in a new window.")){
                				url = 'settings.py?topic=arc';
                				window.open(url,'_blank','width=800,height=600'); // popup the setttings window
                			} 
                		}
                    };
                });
    	} 
    
    // Ask the user she wants to submit with a default proxy certificate and very limited authority.
    function check_proxy(){
    	var submit_without_proxy = true;
    	var settings_page = 'settings.py?output_format=json;topic=arc';

    	$.ajax({
    	    async: false, // disable the asynchronous call back.  
    	    dataType: 'json',
    	    url: settings_page,
    	    success :
    	function(jsonRes, textStatus){
                	for(i=0; i<jsonRes.length; i++){
                		if(jsonRes[i].object_type=="warning"){
                			msg = "No valid ARC proxy certificate."+jsonRes[i].text +
                			"\n\n Do you wish to submit the job using a default proxy "+ 
                			"certificate with limited privileges?"; 
                			submit_without_proxy = confirm(msg);
                		}
                    };
                }
    	});
                return submit_without_proxy;
    	}
    
    // show the specified fields
    function show_fields(fields){
        $(".job_fields").filter(
            function(){
                return (fields.indexOf($(this).attr("id")) != -1);
            }).show();
    }
        
    // Get arc resource information from the arc resources page and show the queues on the submit job page. 
    function load_arc_resources(){
        var arc_resource_page = "arcresources.py?output_format=json";
        //$("div#RESOURCE #arcresources").remove();
        $("div#RESOURCE div[id!=arcresources]").after("<div id='arcresources' class='scrollselect' style='display: none;'><img src='/images/icons/spinner.gif' title='Loading nordugrid queues'/>  </div>");
        //$("div#arcresources").show(); // and show it
        $.getJSON(arc_resource_page,{}, 
            function(jsonRes, textStatus){
                html_resource_list = "";
                for(i=0; i<jsonRes.length; i++){
                    if(jsonRes[i].object_type=="resource_list"){ 
                        resource_list = jsonRes[i].resources;
                        for(j=0; j < resource_list.length; j++){
                            html_resource_list += "<input type='checkbox' name='RESOURCE' value='"+resource_list[j].name+"'>"+resource_list[j].name+"<br />";
                        }
                    }
                };
		
		$("div#RESOURCE #arcresources").empty(); // delete the waiting icon
		$("div#RESOURCE #arcresources").append(html_resource_list); // add the resource list
		    });
    }

    // Update the list of target resources
    function update_resources(jobtype){
    	if(jobtype == "arc"){
    		$("div#RESOURCE #arcresources").show(); // show arc resources
    		$("div#RESOURCE div[id!=arcresources]").hide(); // hide mig resources
	    
    		
    	}else{
    		$("div#RESOURCE div[id!=arcresources]").show(); // show mig resources
    		$("div#RESOURCE #arcresources").hide(); // hide arc resources	
    	}
    	
    	// uncheck the target resources
    	$("input[name=RESOURCE]").each(function(i){
    		$(this).attr("checked",false);
    	});
    }

$(document).ready( function() {
   
// load arc resource queues
	load_arc_resources();
	
// When the job type is changed we update the RE options
     $("select[name=JOBTYPE] option").click(
        function(){
		// if the user wants to run on arc we check if she has uploaded an arc proxy cert
	        if($(this).val()=="arc"){
	        	validate_proxy_certificate(); // Check if there is valid proxy cert for arc.
	        	$("div#VGRID").hide(); // hide the VGRID entry
            }
	        else{
	        	$("div#VGRID").show();
	        }
		
	        update_runtime_env($(this).val());
	    	update_resources($(this).val());
            	
        }
     );

     
  // When clicking the submit job button. If it is an arc job check the proxy.
     $("form#miginput").submit(
    		 function(){
    			 var index = $("select[name=JOBTYPE]").attr("selectedIndex");
    			 var selected_jobtype = $("select[name=JOBTYPE]").attr("options")[index].value;
    			 if (selected_jobtype == "arc"){
    				 //if(!$("input[name=RESOURCE]:checked").length){ // Check the number of selected resources
    					//alert("Please select an ARC cluster to target.")
    					//return false;
    				  //}
    				 
       				return check_proxy(); 
    			 }				 
    		 });
    
     // Events relating to simple/advance view
    $("#advanced").hover(
        function(){
            $(this).css('cursor','pointer');
            //$(this).css({"color":"red"});
            $(this).css({"font-size":"101%%"});
        },
        function(){
            $(this).css('cursor','pointer');
            //$(this).css({"color":"black"});
            $(this).css({"font-size":"100%%"});
        }
    );
    $("#advanced").toggle(
        function () {
            $(this).html("<b><u>Show less options</u></b>");
            $(".job_fields").show();
            //show_fields(simple_view);
            },
        function () {
            $(this).html("<b><u>Show more options</u></b>");
            $(".job_fields").hide();
            show_fields(simple_view);
            }
        );
  });
  
  /*    
    
    // launch the file chooser 
    $( ".file_chooser" ).click( function() {
        var field = $(this).attr("field");
        // we define the callback function to contain the value of the field we eventually wish to update
        var callback = function(path) {
                                $("textarea#"+field).append(path + "\\n");
                                };
        open_chooser("Select "+$(this).attr("name"),
                             callback, false);
          });
	  
    });

*/