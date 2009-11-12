if (jQuery) (function($){
  
	$.fn.tagName = function() {
    return this.get(0).tagName;
	}
	
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

		// TODO: fix this to redo request properly.
		function reload(path) {
			document.location = '/cgi-bin/fm.py';
		}

		function copy(src, dst) {
									
			var flag = '';
						
			// Handle directory copy, set flag and alter destination path.
			if (clipboard['is_dir']) {
				
				flag = 'r';				
				// Extract last directory from source
				dst += src.split('/')[src.split('/').length-2];
			}
			if (dst == '') {
				dst = '.';
			}
			
			//alert('['+src+'] ['+dst+']')
			$.getJSON('/cgi-bin/cp.py',
								{ src: src, dst: dst, output_format: 'json', flags: flag },
								function(jsonRes, textStatus) {
									
									$($('#cmd_dialog').dialog(okDialog));
									$($('#cmd_dialog').dialog('open'));
									
									if (jsonRes.length > 3) {
										for(var i=2; jsonRes.length; i++) {
											$($('#cmd_dialog').html('<p>Error:</p>'+jsonRes[i].text));
										}										
									} else {										
										$($('#cmd_dialog').html('<p>Copied: '+src+'</p><p>To: '+dst+'</p>'));
										reload();
									}
								}
			)
			
		}
		
		function move(src, dst) {
									
			var flag = '';
						
			// Handle directory copy, set flag and alter destination path.
			if (clipboard['is_dir']) {
				
				flag = 'r';				
				// Extract last directory from source
				dst += src.split('/')[src.split('/').length-2];
			}
			if (dst == '') {
				dst = '.';
			}
			
			//alert('['+src+'] ['+dst+']')
			$.getJSON('/cgi-bin/mv.py',
								{ src: src, dst: dst, output_format: 'json', flags: flag },
								function(jsonRes, textStatus) {
																		
									if (jsonRes.length > 3) {
										for(var i=2; jsonRes.length; i++) {
											$($('#rename_dialog').append('<p>Error:</p>'+jsonRes[i].text));
										}										
									} else {										
										$($('#rename_dialog').append('<p>Copied: '+src+'</p><p>To: '+dst+'</p>'));
										//reload();
										$("#rename_dialog").dialog('close');
									}
								}
			)
			
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
			submit:	function (action, el, pos) { 
			
				$.getJSON('/cgi-bin/submit.py',
									{ path: $(el).attr(pathAttribute), output_format: 'json' },
									function(jsonRes, textStatus) {
										
										$($('#cmd_dialog').dialog(okDialog));
										$($('#cmd_dialog').dialog('open'));
										
										for(var i=0; i<jsonRes.length; i++) {
											if (jsonRes[i]['object_type'] == 'submitstatuslist') {
												for(j=0; j<jsonRes[i]['submitstatuslist'].length; j++) {
													
													if (jsonRes[i]['submitstatuslist'][j]['status']) {
														$($('#cmd_dialog').html('<p>Submitted "'
																										+jsonRes[i]['submitstatuslist'][j]['name']
																										+'"</P>'
																										+'<p>Job identfier: "'+jsonRes[i]['submitstatuslist'][j]['job_id']
																										+'"</p>'));
													} else {
														$($('#cmd_dialog').html('<p>Failed submitting:</p><p>'
																										+jsonRes[i]['submitstatuslist'][j]['name']
																										+' '+jsonRes[i]['submitstatuslist'][j]['message']
																										+'</p>'));
													}													
													
												}
											}
										}
										
									}
				);
			
			},
			copy: 	function (action, el, pos) {
				clipboard['is_dir'] = $(el).hasClass('directory');
				clipboard['path']		= $(el).attr(pathAttribute);
			},
			paste: 	function (action, el, pos) {
				copy(clipboard['path'], $(el).attr(pathAttribute));
				reload();
			},
			rm:			function (action, el, pos) {
			
				$.getJSON('/cgi-bin/rm.py',
									{ path: $(el).attr(pathAttribute), output_format: 'json' },
									function(jsonRes, textStatus) {
										
										$($('#cmd_dialog').dialog(okDialog));
										$($('#cmd_dialog').dialog('open'));
										
										if (jsonRes.length > 3) {
											
											for(var i=2; i<jsonRes.length; i++) {
												$($('#cmd_dialog').html('<p>Error:</p>'+jsonRes[i].text));
											}
																						
										} else {
											$($('#cmd_dialog').html('<p>nice!</p>'));
											reload();
										}
									}
				);				
			
			},
			// Note: this uses rm.py backend and not rmdir.py since recursive deletion
			//       usually the behaviour one expects when deleting a folder in a
			//       filemanager gui.
			rmdir:	function (action, el, pos) {

				$($('#cmd_dialog').dialog(okDialog));

				$.getJSON('/cgi-bin/rm.py',
									{ path: $(el).attr(pathAttribute), flags: 'r', output_format: 'json' },
									function(jsonRes, textStatus) {
										
										$($('#cmd_dialog').dialog('open'));
										
										if (jsonRes.length > 3) {
											for(var i=2; jsonRes.length; i++) {
												$($('#cmd_dialog').html('<p>Error:</p>'+jsonRes[i].text));												
											}
																						
										} else {
											$($('#cmd_dialog').html('<p>nice!</p>'));
											reload();
										}
									}
				);
			},
			upload: function (action, el, pos) {
								$($("#upload_dialog").dialog({buttons: {Upload: function() { $('#myForm').submit();  }, Cancel: function() {$(this).dialog('close');} }, autoOpen: false, closeOnEscape: true, modal: true}));
								$($('#upload_dialog').dialog('open'));
								// TODO: upload + reload();
							},
			mkdir:  function (action, el, pos) {
								
								$("#mkdir_dialog").dialog('destroy');
								$("#mkdir_dialog").dialog({ buttons: {
																								Ok: function() {					
																											$.getJSON('/cgi-bin/mkdir.py',
																																{ path: $(el).attr(pathAttribute)+'/'+$('#mk_name').val(), output_format: 'json' },
																																function(jsonRes, textStatus) {																																																		
																																	if (jsonRes.length > 3) {																																			
																																		for(var i=2; jsonRes.length; i++) {
																																			$($('#mkdir_dialog').append('<p>Error:</p>'+jsonRes[i].text));
																																		}																																														
																																	} else {																																																																					
																																		$('#mkdir_dialog').dialog('close');
																																		reload();
																																	}
																																}
																												);																										
																										},
																								Cancel: function() {$(this).dialog('close');}
																							},
																							autoOpen: false,
																							closeOnEscape: true,
																							modal: true}
								
																						);
								$("#mkdir_dialog").dialog('open');
							},
							
			// NOTE: it seems that the mv.py backend does not allow for folders to be moved so only
			//       renaming of files works.
			rename: function(action, el, pos) {
				
								$("#rename_dialog").dialog('destroy');
								$("#rename_dialog").dialog({ buttons: {
																								Ok: function() {
																									//alert('rename!');
																									move($(el).attr(pathAttribute), $('#rn_name').val());

																								},
																								Cancel: function() {$(this).dialog('close');}
																							},
																							autoOpen: false,
																							closeOnEscape: true,
																							modal: true}
								
																						);
								$("#rename_dialog").dialog('open');
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
												'<li class="directory collapsed" title=""><div>/</div>';
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
												
						path = t+listing[i]['name'];
						
            if (is_dir) {
              base_css_style = 'directory';

							//folders +=  '<li class="'+base_css_style+' collapsed" title="'+t+'/'+listing[i]['name']+'/"><div>'
							path += '/';
							folders +=  '<li class="'+base_css_style+' collapsed" title="'+path+'	"><div>'
                          + listing[i]['name']
													+'</div></li>\n';
							dir_prefix = '__';
							
            }
						
						$('table tbody').html = '';						
						$('table tbody').append($('<tr></tr>')
													.attr('title', path)
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
					
					// Prefix '/' for the visual presentation of the current path.
					if (t.substr(0,1)=='/') {
						addressbar.find('input').val(t);	
					} else {
						addressbar.find('input').val('/'+t);	
					}
					
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
					var spacerHeight = $("#fm_filelisting").height() - $(".fm_files").height();
					if (spacerHeight < 0) {
						spacerHeight = $(".fm_files").height() - $("#fm_filelisting").height()-20;
						$('.fm_files').append('<div class="filespacer" style="height: '+spacerHeight+'px ;" title="'+t+'"></div>');
						$("div.filespacer").contextMenu({ menu: 'folder_context'},
                                            function(action, el, pos) {
																							
																							(options['actions'][action])(action, el, pos);                                            
                                            });
						
					}
					
					// Associate context-menus
          $("tr.directory, li.directory div").contextMenu({ menu: 'folder_context'},
                                            function(action, el, pos) {
																							if ($(el).tagName() == 'DIV') {
																								(options['actions'][action])(action, el.parent(), pos);
																							} else {
																								(options['actions'][action])(action, el, pos);
																							}																							
                                            });
          
          $("tr.file").contextMenu({ menu: 'file_context'},
                                            function(action, el, pos) {
																							(options['actions'][action])(action, el, pos);																						
                                            });
					
					// Associate drag'n'drop
					$('tr.file, tr.directory, li.directory').draggable({cursorAt: { cursor: 'move', top: 0, left: -10 },
																														  distance: 5,
																															helper: function(event) {
																																				return $('<div style="display: block;">&nbsp;</div>')
																																							.attr('title', $(this).attr('title'))
																																							.attr('class', $(this).attr('class'))
																																							.css('width', '20px');
																																			}
																			}
													);
					
					$('tr.directory, li.directory').droppable({
						greedy: true,
						drop: function(event, ui) {
							clipboard['is_dir'] = $(ui.helper).hasClass('directory');
							clipboard['path']		= $(ui.helper).attr(pathAttribute);
							copy($(ui.helper).attr('title'), $(this).attr('title'));
						}
					});	
          										
					// Binds: Expands and a call to showbranch
					// or
					// Binds: Collapse
					bindBranch(folder_pane);					
										
        });

      }
      
      function bindBranch(t) {
				$(t).find('LI').bind(options.folderEvent,
					
					function() {
						if( $(this).hasClass('directory') ) {
							if( $(this).hasClass('collapsed') ) {
								// Expand
								if( !options.multiFolder ) {
									$(this).parent().find('UL').slideUp({ duration: options.collapseSpeed, easing: options.collapseEasing });
									$(this).parent().find('LI.directory').removeClass('expanded').addClass('collapsed');
								}
								$(this).find('UL').remove(); // cleanup
								// Go deeper
								//showBranch( $(this), escape($(this).attr('title').match( /.*\// )) );
								showBranch( $(this), $(this).attr('title') );
								$(this).removeClass('collapsed').addClass('expanded');
							} else {
								// Collapse
								$(this).find('UL').slideUp({ duration: options.collapseSpeed, easing: options.collapseEasing });
								$(this).removeClass('expanded').addClass('collapsed');
							}
						} else {
							$(this).attr('title');
						}
						return false;
					}
				);
				
        // Prevent A from triggering the # on non-click events
        if( options.folderEvent.toLowerCase != 'click' ) {
					$(t).find('LI').bind('click', function() { return false; });
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
