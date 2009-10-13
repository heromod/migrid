if (jQuery) (function($){
  
  $.fn.filemanager = function(user_options) {

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
        loadMessage: 'Loading...'
    };
    var options = $.extend(defaults, user_options);

    return this.each(function() {
      obj = $(this);
            
      function showTree(folder_pane, t) {
        
        //var folder_pane = $('.fm_folders', obj);
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
                  
          var folders = '<ul class="jqueryFileTree">';          
          
          /*
          var files = '<table>'+
                      '<thead>'+
                      ' <tr><td>&nbsp;</td><td>&nbsp;</td><td>Name</td><td>Size</td><td>Date Modified</td></tr>'+
                      ' </thead>'+
                      ' <tbody>';*/
                      
          var files = '<ul class="jqueryFileList">';
          
          var total_file_size = 0;
          var file_count = 0.0;          
          var is_dir = false;
          var base_css_style = 'file';
          
          for (i=0;i<listing.length;i++) {
            
            is_dir = listing[i]['type'] == 'directory';
            base_css_style = 'file';
            if (is_dir) {
              base_css_style = 'directory';
              folders +=  '<li class="'+base_css_style+' collapsed">'+
                          ' <a href="#" rel="'+t+'/'+listing[i]['name']+'/">'+listing[i]['name']+'</a>'+
                          '</li>\n';
            }
            /*
            files +=  '<tr>'+
                      '<td class="bulk"><input type="checkbox" /></td>'+
                      ' <td class="'+base_css_style+' ext_'+listing[i]['ext']+'">&nbsp;</td>'+
                      ' <td>'+listing[i]['name']+'</td>'+
                      ' <td style="text-align: right;">'+pp_bytes(listing[i]['size'])+'</td>'+
                      ' <td>'+pp_date(listing[i]['create_time'])+'</td>'+
                      '</tr>';*/
            files +=  '<li class="'+base_css_style+' ext_'+listing[i]['ext']+'">'+
// TODO: expand the backend to send filesize with
//                      ' <span class="size">'+pp_bytes(listing[i]['size'])+'</span>'+
                      ' <span class="size">'+pp_bytes(1)+'</span>'+
// TODO: expand the backd to send this infor with
//                      ' <span class="cdate">'+pp_date(listing[i]['create_time'])+'</span>'+
                      ' <span class="cdate">create time</span>'+
                      ' <span class="bulk"><input type="checkbox" /></span>'+
                      ' <span class="name">'+listing[i]['name']+'</span>'+
                      
                      '</li>';

            total_file_size += listing[i]['size'];
            file_count++;
            
          }
          folders, files += '</ul>';
          
          //files += '</ul>'
          /*files +=  ' </tbody>'+
                    '</table>';*/
                    
          addressbar.find('input').val(t);
          folder_pane.removeClass('wait').append(folders);
          file_pane.removeClass('wait').html(files);
          statusbar.html(file_count+' files in current folder of total '+pp_bytes(total_file_size)+' bytes in size.');
  
          if( options.root == t ) {
            folder_pane.find('UL:hidden').show();
          } else {
            folder_pane.find('UL:hidden').slideDown({ duration: options.expandSpeed, easing: options.expandEasing });
          }
          
          /* Associate context-menus */
          $(".directory").contextMenu({ menu: 'folder_context'},
                                            function(action, el, pos) {
                                            alert(
                                                'Action: ' + action + ',' +
                                                'Element ID: ' + $(el).find('a').attr('rel') + ',' + el.find('li') +
                                                'X: ' + pos.x + '  Y: ' + pos.y + ' (relative to element),' +
                                                'X: ' + pos.docX + '  Y: ' + pos.docY+ ' (relative to document)'
                                                );
                                            });
          
          $(".file").contextMenu({ menu: 'file_context'},
                                            function(action, el, pos) {
                                            alert(
                                                'Action: ' + action + ',' +
                                                'Element ID: ' + $(el).attr('class') + ',' + el.find('li') +
                                                'X: ' + pos.x + '  Y: ' + pos.y + ' (relative to element),' +
                                                'X: ' + pos.docX + '  Y: ' + pos.docY+ ' (relative to document)'
                                                );
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
      $('.fm_files', obj).html('<ul class="jqueryFileTree start"><li class="wait">' + options.loadMessage + '<li></ul>');
      
      // Get the initial file list

      
      showTree( $('.fm_folders', obj), escape(options.root) );
      

    });

 };
 
})(jQuery);
