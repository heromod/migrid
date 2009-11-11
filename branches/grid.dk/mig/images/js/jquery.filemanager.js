if (jQuery) (function($){
  
  $.fn.filemanager = function(user_options) {
	
		var pathAttribute = 'title';
		var clipboard = new Array({'is_dir':false, 'path':''});
		
		// Note: max-height is broken on autoHeight this is noted as a bug:
		//       http://dev.jqueryui.com/ticket/4820
		//       The stated workaround is used in cmdHelper.
		var dialogOptions = { width: '620px', autoOpen: false, closeOnEscape: true, modal: true}
		var okDialog			= { buttons: {Ok: function() {$(this).dialog('close');} }, width: '620px', autoOpen: false, closeOnEscape: true, modal: true}
		var closeDialog		= { buttons: {Close: function() {$(this).dialog('close');} }, width: '620px', autoOpen: false, closeOnEscape: true, modal: true}		

		function doubleClickEvent(el) {
			if($(el).hasClass('directory')) {
				// go deeper
			} else {
				document.location = '/cert_redirect/' + $(el).attr(pathAttribute);
			}
		}

		function cmdHelper(el, dialog, url) {
									
			$.getJSON(url,
								{ path: $(el).attr(pathAttribute), output_format: 'json' },
								function(jsonRes, textStatus) {
									
									var file_output = '';
									for(i=0;i<jsonRes.length; i++) {
										
										if (jsonRes[i].object_type=='file_output') {
											
											for(j=0; j<jsonRes[i].lines.length; j++) {
												file_output += jsonRes[i].lines[j]+"\n";
											}
											
										}
									}
									
									$($(dialog).dialog(closeDialog));
									$(dialog).html('<div style="max-height: 480px;"><pre>'+file_output+'</pre></div>');
									$($(dialog).dialog('open'));
									
								}
			)

		}

		// Callback helpers for context menu
		var callbacks = {
			
			show: 	function (action, el, pos) { document.location = '/cert_redirect/' + $(el).attr(pathAttribute) },
			edit: 	function (action, el, pos) {},
			cat:		function (action, el, pos) { cmdHelper(el, '#cmd_dialog', '/cgi-bin/cat.py'); },
			head:		function (action, el, pos) { cmdHelper(el, '#cmd_dialog', '/cgi-bin/head.py'); },
			tail:		function (action, el, pos) { cmdHelper(el, '#cmd_dialog', '/cgi-bin/tail.py'); },
			submit:	function (action, el, pos) { alert('wait'); },
			copy: 	function (action, el, pos) {
				clipboard['is_dir'] = $(el).hasClass('directory');
				clipboard['path']		= $(el).attr(pathAttribute);
			},
			paste: 	function (action, el, pos) {
				
				var flag = '';
				var pathFix = '';
				
				var src, dst = '';
				
				if (clipboard['is_dir']) {
					flag = 'r';
					pathFix = '/';
				}
				
				dst = $(el).attr(pathAttribute)+clipboard['path'];
				src = clipboard['path'];
				
				alert('From= '+src.substring(1)+' To= '+dst.substring(1));
				$.getJSON('/cgi-bin/cp.py',
									{ src: src.substring(1), dst: dst.substring(1), output_format: 'json', flags: flag },
									function(jsonRes, textStatus) {
										
										$($('#cmd_dialog').dialog(okDialog));
										$($('#cmd_dialog').dialog('open'));
										
										if (jsonRes.length > 3) {

											for(var i=2; jsonRes.length; i++) {
												$($('#cmd_dialog').html('<p>Error:</p>'+jsonRes[i].text));
											}
											
										} else {
											// TODO: "refresh"
											$($('#cmd_dialog').html('<p>Copied: '+clipboard['path']+'</p><p>To: '+$(el).attr(pathAttribute)+'</p>'));
										}
									}
				)	
				
			},
			rm:			function (action, el, pos) {
							
				$.getJSON('/cgi-bin/rm.py',
									{ path: $(el).attr(pathAttribute), output_format: 'json' },
									function(jsonRes, textStatus) {
										
										$($('#cmd_dialog').dialog(okDialog));
										$($('#cmd_dialog').dialog('open'));
										
										if (jsonRes.length > 3) {
											
											for(var i=2; jsonRes.length; i++) {
												$($('#cmd_dialog').html('<p>Error:</p>'+jsonRes[i].text));
											}
																						
										} else {
											
											// TODO: "refresh"
											$($('#cmd_dialog').html('<p>nice!</p>'));
											
										}
									}
				);
			
			},
			rmdir:	function (action, el, pos) {
				$($('#cmd_dialog').dialog(okDialog));
				$.getJSON('/cgi-bin/rmdir.py',
									{ path: $(el).attr(pathAttribute), output_format: 'json' },
									function(jsonRes, textStatus) {
										
										$($('#cmd_dialog').dialog('open'));
										
										if (jsonRes.length > 3) {
											for(var i=2; jsonRes.length; i++) {
												$($('#cmd_dialog').html('<p>Error:</p>'+jsonRes[i].text));												
											}
																						
										} else {
											// ok
											// TODO: "refresh"
											$($('#cmd_dialog').html('<p>nice!</p>'));
										}
									}
				);
			},
			upload: function (action, el, pos) {
								$($("#upload_dialog").dialog({buttons: {Upload: function() { $('#myForm').submit();  }, Cancel: function() {$(this).dialog('close');} }, autoOpen: false, closeOnEscape: true, modal: true}));
								$($('#upload_dialog').dialog('open'));
							},
			mkdir:  function (action, el, pos) {
				
								$($("#mkdir_dialog").dialog({ buttons: {
																								Ok: function() {					
																											$.getJSON('/cgi-bin/mkdir.py',
																																{ path: $(el).attr(pathAttribute)+'/'+$('#name').val(), output_format: 'json' },
																																function(jsonRes, textStatus) {																																																		
																																	if (jsonRes.length > 3) {																																			
																																		for(var i=2; jsonRes.length; i++) {
																																			$($('#mkdir_dialog').append('<p>Error:</p>'+jsonRes[i].text));
																																		}																																														
																																	} else {																																			
																																		// TODO: "refresh"
																																		$('#mkdir_dialog').dialog('close');
																																	}
																																}
																												);																										
																										},
																								Cancel: function() {$(this).dialog('close');}
																							},
																							autoOpen: false,
																							closeOnEscape: true,
																							modal: true}
								
																						));
								$($("#mkdir_dialog").dialog('open'));
							}
		}

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
      function showBranch(folder_pane, t) {
        
        var file_pane   = $('.fm_files', obj);        
        var statusbar   = $('.fm_statusbar', obj);
        var addressbar  = $('.fm_addressbar', obj);
        
        $(folder_pane).addClass('wait');
        $(".jqueryFileTree.start").remove();
				
        $.getJSON(options.connector, { path: t }, function(jsonRes, textStatus) {
          
					// Place ls.py output in listing array
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
					if (t=='/') {
						folders +=	'<ul class="jqueryFileTree">'+
												'<li class="directory collapsed" title="//"> <a title="//" href="#">/</a>';
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
					var path = '';
          
          for (i=0;i<listing.length;i++) {
            
            is_dir = listing[i]['type'] == 'directory';
            base_css_style	= 'file';
						dir_prefix			= '';
						
						// Stats for the statusbar
						file_count++;
            total_file_size += listing[i]['file_info']['size'];
												
						path = t+'/'+listing[i]['name'];
						
            if (is_dir) {
              base_css_style = 'directory';
              folders +=  '<li class="'+base_css_style+' collapsed" title="'+t+'/'+listing[i]['name']+'/">'+
                          ' <a href="#" title="'+t+'/'+listing[i]['name']+'/">'+listing[i]['name']+'</a>'+
                          '</li>\n';
							dir_prefix = '__';
							path += '/';
            }
						
						$('table tbody').html = '';						
						$('table tbody').append($('<tr></tr>')
													.attr('title', t+listing[i]['name'])
													.addClass(base_css_style)
													.addClass('ext_'+listing[i]['ext'])
													.dblclick( function() { doubleClickEvent(this); } )
													.append(
														$(
															'<td style="padding-left: 20px;"><div>'+dir_prefix+listing[i]['name']+'</div>'+listing[i]['name']+'</td>'+
															'<td><div>'+listing[i]['file_info']['size']+'</div>'+pp_bytes(listing[i]['file_info']['size'])+'</td>'+
															'<td><div>'+listing[i]['file_info']['ext']+'</div>'+listing[i]['file_info']['ext']+'</td>'+
															'<td><div>'+listing[i]['file_info']['created']+'</div>'+pp_date(listing[i]['file_info']['created'])+'</td>'
														)
													));
										
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
					
					// Update statusbar
          statusbar.html(file_count+' files in current folder of total '+pp_bytes(total_file_size)+' bytes in size.');
  
          if( options.root == t ) {
            folder_pane.find('UL:hidden').show();
          } else {
            folder_pane.find('UL:hidden').slideDown({ duration: options.expandSpeed, easing: options.expandEasing });
          }
          
					/* UI stuff: contextmenu, drag'n'drop. */
					
					// Create an element for the whitespace below the list of files in the file pane
					var spacerHeight = $(".fm_files").height() - $("#fm_filelisting").height();
					if (spacerHeight > 0) {
						$('.fm_files').append('<div class="filespacer" style="height: '+spacerHeight+'px ;"><div style="display: none;">'+t+'</div></div>');
						$("div.filespacer").contextMenu({ menu: 'folder_context'},
                                            function(action, el, pos) {																							
																							(options['actions'][action])(action, el, pos);                                            
                                            });
						
					}
					
					// Associate context-menus
          $(".directory").contextMenu({ menu: 'folder_context'},
                                            function(action, el, pos) {
																							(options['actions'][action])(action, el, pos);                                            
                                            });
          
          $("tr.file").contextMenu({ menu: 'file_context'},
                                            function(action, el, pos) {
																							(options['actions'][action])(action, el, pos);																						
                                            });
					
					// Associate drag'n'drop
					$('tr.file, tr.directory, li.directory a').draggable({cursorAt: { cursor: 'move', top: 0, left: -10 },
																																helper: function(event) {
																																					return $('<div style="display: block;">&nbsp;</div>')
																																								.attr('title', $(this).attr('title'))
																																								.attr('class', $(this).attr('class'))
																																								.css('width', '20px');
																																				}
																			}
													);
					
					$('tr.directory, li.directory a').droppable({
						drop: function(event, ui) {							
							alert('Dragging: '+$(ui.helper).attr('title') + ' to: '+ $(this).attr('title')+'.');
						}
					});	
          										
					// Binds: Expands and a call to showbranch
					// or
					// Binds: Collapse
					bindBranch(folder_pane);					
										
        });

      }
      
      function bindBranch(t) {
        $(t).find('LI A').bind(options.folderEvent,
					
					function() {
						if( $(this).parent().hasClass('directory') ) {
							if( $(this).parent().hasClass('collapsed') ) {
								// Expand
								if( !options.multiFolder ) {
									$(this).parent().parent().find('UL').slideUp({ duration: options.collapseSpeed, easing: options.collapseEasing });
									$(this).parent().parent().find('LI.directory').removeClass('expanded').addClass('collapsed');
								}
								$(this).parent().find('UL').remove(); // cleanup
								// Go deeper
								alert($(this).parent().attr('class'));
								showBranch( $(this).parent(), escape($(this).attr('title').match( /.*\// )) );
								$(this).parent().removeClass('collapsed').addClass('expanded');
							} else {
								// Collapse
								$(this).parent().find('UL').slideUp({ duration: options.collapseSpeed, easing: options.collapseEasing });
								$(this).parent().removeClass('expanded').addClass('collapsed');
							}
						} else {
							h($(this).attr('title'));
						}
						return false;
					}
				);
				
        // Prevent A from triggering the # on non-click events
        if( options.folderEvent.toLowerCase != 'click' ) {
					$(t).find('LI A').bind('click', function() { return false; });
				}
				
			}
			    			
      // Base sorting on the content of the hidden <div> element
			var myTextExtraction = function(node) {  
					return node.childNodes[0].innerHTML; 
			} 
			$('.fm_files table', obj).tablesorter({widgets: ['zebra'],
																						textExtraction: myTextExtraction,
																						sortColumn: 'Name'});
			
			// Loading message
      $('.fm_folders', obj).html('<ul class="jqueryFileTree start"><li class="wait">' + options.loadMessage + '<li></ul>');
      showBranch( $('.fm_folders', obj), escape(options.root) );
			
    });

 };
 
})(jQuery);
