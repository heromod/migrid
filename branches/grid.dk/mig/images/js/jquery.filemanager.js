if (jQuery) (function($){
  
  $.fn.filemanager = function(user_options) {
	
		var jeojepjep = '';

		function cmdHelper(el, dialog, url) {
				
			$($(dialog).dialog({ closeOnEscape: true, modal: true }));
			$.getJSON(url,
								{ path: $(el).attr('id'), output_format: 'json' },
								function(jsonRes, textStatus) {
									var file_output = '';
									for(i=0;i<jsonRes.length; i++) {
										
										if (jsonRes[i].object_type=='file_output') {
											
											for(j=0; j<jsonRes[i].lines.length; j++) {
												file_output += jsonRes[i].lines[j]+"\n";
											}
											
										}
									}
									$(dialog).html('<pre>'+file_output+'</pre>');
								}
			)
			
		}

		// Callback helpers for context menu
		var callbacks = {
			
			show: 	function (action, el, pos) { document.location = '/cert_redirect/' + $(el).attr('id') },
			edit: 	function (action, el, pos) {},
			cat:		function (action, el, pos) { cmdHelper(el, '#cmd_dialog', '/cgi-bin/cat.py'); },
			head:		function (action, el, pos) { cmdHelper(el, '#cmd_dialog', '/cgi-bin/head.py'); },
			tail:		function (action, el, pos) { cmdHelper(el, '#cmd_dialog', '/cgi-bin/tail.py'); },
			copy: 	function (action, el, pos) {
				jepjepjep = $(el).attr('id')
			},
			paste: 	function (action, el, pos) {
				// todo perform the copy
				$.getJSON('/cgi-bin/cp.py',
									{ src: jepjepjep, dst: $(el).attr('id'), output_format: 'json' },
									function(jsonRes, textStatus) {
										if (jsonRes.length > 3) {
											// ok
										} else {
											// error
											$($('#cmd_dialog').dialog({ closeOnEscape: true, modal: true }));
										}
									}
				)	
				
			},
			rm:			function (action, el, pos) {
							
				$.getJSON('/cgi-bin/rm.py',
									{ path: $(el).attr('id'), output_format: 'json' },
									function(jsonRes, textStatus) {
										if (jsonRes.length > 3) {
											// ok
										} else {
											// error
											$($('#cmd_dialog').dialog({ closeOnEscape: true, modal: true }));
										}
									}
				);
			
			},
			rmdir:	function (action, el, pos) {
				$($('#cmd_dialog').dialog({ closeOnEscape: true, modal: true }));
				$.getJSON('/cgi-bin/rmdir.py',
									{ path: $(el).attr('id'), output_format: 'json' },
									function(jsonRes, textStatus) {
										if (jsonRes.length > 3) {
											// ok
										} else {
											// error
										}
									}
				);
			},
			upload: function (action, el, pos) {
								$($("#upload_dialog").dialog({ closeOnEscape: true, modal: true }));								
							},
			mkdir:  function (action, el, pos) { $($("#mkdir_dialog").dialog({ closeOnEscape: true, modal: true })); }
		}

		/*show: 	'/cert_redirect/',
		edit: 	'/cgi-bin/editor.py?path=',
		cat:		'/cgi-bin/cat.py?path=',
		head:		'/cgi-bin/head.py?path=',
		tail:		'/cgi-bin/tail.py?path=',
		copy: 	'',
		rm:			'/cgi-bin/rm.py?path=',
		rmdir:	'/cgi-bin/rmdir.py?path='
		*/
    var defaults = {
        root: '/',      
        connector: 'somewhere.py',
        param: 'path',
        folderEvent: 'click',  
        expandSpeed: 500,
        collapseSpeed: 500,
        expandEasing: null,
  			collapseEasing: null,
        multiFolder: true,
        loadMessage: 'Loading...',
				actions: callbacks				
    };
    var options = $.extend(defaults, user_options);

    return this.each(function() {
      obj = $(this);
            						
			// Create the tree structure on the left and populates the table list of files on the right
      function showTree(folder_pane, t) {
        
        var file_pane   = $('.fm_files', obj);
        var toolbar     = $('.fm_toolbar', obj);
        var statusbar   = $('.fm_statusbar', obj);
        var addressbar  = $('.fm_addressbar', obj);
        
        $(folder_pane).addClass('wait');
        $(".jqueryFileTree.start").remove();

				
        $.getJSON(options.connector, { path: t }, function(jsonRes, textStatus) {
          
          var listing = new Array();
          var i,j;
          
          for(i=0;i<jsonRes.length; i++) {
            
            if (jsonRes[i].object_type=='dir_listings') {
              
              for(j=0; j<jsonRes[i].dir_listings.length; j++) {
                listing = listing.concat(jsonRes[i].dir_listings[j].entries);
              }
              
            }
          }
                  
          var folders = '';

					// Root node
					//if (options.root == t) {
					if (t=='/') {
						folders += '<ul class="jqueryFileTree"><li class="directory collapsed"> <a rel="//" href="#">/</a>';
					}
					
					// Regular nodes from herone after
					folders += '<ul class="jqueryFileTree">';          
          var files = '<ul class="jqueryFileList">';
					$('table tbody').html('');
          
          var total_file_size = 0;
          var file_count = 0.0;          
          var is_dir = false;
          var base_css_style = 'file';
					var dir_prefix = '';
          
          for (i=0;i<listing.length;i++) {
            
            is_dir = listing[i]['type'] == 'directory';
            base_css_style = 'file';
						
						// Stats for the statusbar
						file_count++;
            total_file_size += listing[i]['file_info']['size'];
						
						dir_prefix = '';
            if (is_dir) {
              base_css_style = 'directory';
              folders +=  '<li class="'+base_css_style+' collapsed">'+
                          ' <a href="#" rel="'+t+'/'+listing[i]['name']+'/">'+listing[i]['name']+'</a>'+
                          '</li>\n';
							dir_prefix = '__';
            }
						
						$('table tbody').html = '';
						$('table tbody').append(
							
						'<tr id="'+t+listing[i]['name']+'" class="'+base_css_style+'">'+
						'<td style="padding-left: 20px;" class="'+base_css_style+' ext_'+listing[i]['ext']+'"><div>'+dir_prefix+listing[i]['name']+'</div>'+listing[i]['name']+'</td>'+
						'<td><div>'+listing[i]['file_info']['size']+'</div>'+pp_bytes(listing[i]['file_info']['size'])+'</td>'+
						'<td><div>'+listing[i]['file_info']['ext']+'</div>'+listing[i]['file_info']['ext']+'</td>'+
						'<td><div>'+listing[i]['file_info']['created']+'</div>'+pp_date(listing[i]['file_info']['created'])+'</td>'+
						'</tr>'                           
                           );
						// Fix the shit above
						//var shitface = '#'+t+listing[i]['name'];
						//$(shitface).addClass(base_css_style);
					
          }
          folders, files += '</ul>';
					
					// End the root node
					if (t=='/') {
						folders += '</li></ul>';
					}
                              
          addressbar.find('input').val(t);
          folder_pane.removeClass('wait').append(folders);
					
					// Inform tablesorter of new data
					var sorting = [[0,0]]; 
					$("table").trigger("update");       
					$("table").trigger("sorton",[sorting]);
					
          statusbar.html(file_count+' files in current folder of total '+pp_bytes(total_file_size)+' bytes in size.');
  
          if( options.root == t ) {
            folder_pane.find('UL:hidden').show();
          } else {
            folder_pane.find('UL:hidden').slideDown({ duration: options.expandSpeed, easing: options.expandEasing });
          }
          
          /* Associate context-menus */
          $(".directory").contextMenu({ menu: 'folder_context'},
                                            function(action, el, pos) {
																							(options['actions'][action])(action, el, pos);                                            
                                            });
          
          $("tr.file").contextMenu({ menu: 'file_context'},
                                            function(action, el, pos) {
																							(options['actions'][action])(action, el, pos);																						
                                            });
          
					bindTree(folder_pane);
        });

      }
      
      function bindTree(t) {
        $(t).find('LI A').bind(options.folderEvent, function() {
          if( $(this).parent().hasClass('directory') ) {
            if( $(this).parent().hasClass('collapsed') ) {
              // Expand
              if( !options.multiFolder ) {
                $(this).parent().parent().find('UL').slideUp({ duration: options.collapseSpeed, easing: options.collapseEasing });
                $(this).parent().parent().find('LI.directory').removeClass('expanded').addClass('collapsed');
              }
              $(this).parent().find('UL').remove(); // cleanup
              showTree( $(this).parent(), escape($(this).attr('rel').match( /.*\// )) );
              $(this).parent().removeClass('collapsed').addClass('expanded');
            } else {
              // Collapse
              $(this).parent().find('UL').slideUp({ duration: options.collapseSpeed, easing: options.collapseEasing });
              $(this).parent().removeClass('expanded').addClass('collapsed');
            }
          } else {
            h($(this).attr('rel'));
          }
          return false;
        });
        // Prevent A from triggering the # on non-click events
        if( options.folderEvent.toLowerCase != 'click' ) $(t).find('LI A').bind('click', function() { return false; });
			}
			
      // Loading message
      $('.fm_folders', obj).html('<ul class="jqueryFileTree start"><li class="wait">' + options.loadMessage + '<li></ul>');
			
      // Get the initial file list
			var myTextExtraction = function(node) {  
					return node.childNodes[0].innerHTML; 
			} 
			$('.fm_files table', obj).tablesorter({widgets: ['zebra'],
																						textExtraction: myTextExtraction,
																						sortColumn: 'Name'});
      showTree( $('.fm_folders', obj), escape(options.root) );
			
    });

 };
 
})(jQuery);
