jQuery(proofreader);
jQuery.ajaxSetup({'cache': false});

function proofreader() {

  var ajax_interface = "../cgi-bin/command.py";
  var diff_provider = "../cgi-bin/diffs.py";
  var projid = "";


  function init() {
    //extract projid from URL
    var url_param_strings = location.search.substring(1).split("&");
    for(var c = 0; c < url_param_strings.length; c++) {
      var pos = url_param_strings[c].indexOf("=");
      if(pos == -1) continue;
      var name = url_param_strings[c].substring(0, pos);
      if(name == "projid")  {
        projid = decodeURIComponent(url_param_strings[c].substring(pos + 1));
      }
    }
    //set up ui width and slider
    var ui_width = 800;
    if(localStorage && localStorage["ui_width"]) {
      ui_width = localStorage["ui_width"];
    }
    $("#slider").slider(
      {value: ui_width, min: 400, max: 1500, step: 25,
       slide: function(ev, ui) {
         $(document).trigger({type:"uiwidth", width:ui.value});},
       stop: function(ev, ui) {
         if(localStorage) localStorage["ui_width"] = ui.value;}});
    $(document).trigger({type:"uiwidth", width:ui_width});
    //asynchrously insert title and guidelines link
    jQuery.getJSON(ajax_interface, { verb:"get_meta", projid: projid},
                   function (ob) {
                     $('#title').text(ob["title"]);
                     if(ob["project_link"])
                       $("#project_link").attr("href", ob["project_link"]);
                     else
                       $("#project_link").remove();});
    //Set all menu_bar links in open in new windows
    $('#menu_bar > a').click(function(event) {
                           window.open($(this).attr('href'));
                           event.preventDefault();});
    //Show pagepicker to start
    page_picker.show();
  }


  (function title_bar() {
    $("#close_interface").button({icons:{primary: "ui-icon-closethick"}, text:false});
    $("#spacer").resizable(
      {handles: "s", minHeight: 16,
       stop: function(event, ui) {
         if(localStorage)
           localStorage["spacer_height"] = ui.size.height;}});
    if(localStorage && localStorage["spacer_height"]) {
      $("#spacer").height(localStorage["spacer_height"]); }
    $(document).bind("uiwidth",
                    function(ob) {$('#title_bar, #spacer').width(ob.width);});
    $(document).bind("page",
                     function(ob) {$("#pageid").text(ob.page_id);});
    $(document).bind(
      "status",
      function(ob) {
        if(ob.status == "clean") $('#status').removeClass("warn").text("Submitted");
        else $('#status').addClass("warn").text("Not submitted");
      });
  })();


  function image_container_func() {

    var current_line = 0;
    var max_line;
    var line_positions;
    var page_id;
    var offset = 0;

    $("#image_container").resizable(
      {handles: "s", minHeight: 100,
       stop: function(event, ui) {
         if(localStorage)
           localStorage["image_container_height"] = ui.size.height;
         select();}});
    if(localStorage && localStorage["image_container_height"]) {
      $("#image_container").height(localStorage["image_container_height"]); }
    $(document).bind("uiwidth",
                     function(ob){$("#image_container").width(ob.width); select();});
    $(document).bind("page", new_page);
    $(document).bind("linechange", function(ob) {select(ob.line);});


    function load_image(page, pos) {
      var url = "../images/blank.png";
      if(page) {
        url = ajax_interface + "?" + jQuery.param({verb: "get_image",
                                                   projid: projid,
                                                   pageid: page});
      }
      var img = $("<img />").attr({'src': url, 'alt': pos});
      function image_load_handler(event) {
        var target = event.currentTarget;
        var pos = target.getAttribute('alt');
        $('#image_container img').eq(pos).replaceWith(target);
        select();
      }
      if (img.get(0).complete || img.get(0).readyState === 4) {
        image_load_handler({currentTarget: img.get(0)});
      }
      else {
        img.load(image_load_handler);
      }
    }


    function new_page(ob) {
      page_id = ob.page_id;
      //only load line_positions for current page_id
      function linepos_handler_factory(_page_id) {
        return function(ob) {
          if(page_id == _page_id) {
            current_line = 0;
            offset = 0;
            line_positions = ob;
            max_line = line_positions && line_positions.length;
            select();
          }};
      }
      jQuery.getJSON(ajax_interface,
                     {projid:projid, pageid:page_id, verb:"get_lines"},
                     linepos_handler_factory(page_id));
      load_image(page_id, 1);
      //handler functions are generated closures to ensure correctly loaded image
      //is not overwritten due to a slow response to a previous ajax call
      function imgload_handler_factory(_page_id, pos) {
        return function(ob) {if(_page_id == page_id) load_image(ob, pos);
                             else load_image(null, pos);};
      }
      jQuery.getJSON(ajax_interface,
                     {projid:projid, pageid:page_id, verb:"get_prev"},
                    imgload_handler_factory(page_id, 0));
      jQuery.getJSON(ajax_interface,
                     {projid:projid, pageid:page_id, verb:"get_next"},
                    imgload_handler_factory(page_id, 2));
    }


    function select(line) {
      if(!line_positions) return;
      // var line = _line != undefined ? _line: current_line;
      if(line == undefined) line = current_line;
      current_line = line;
      line += offset;
      if(line < 0) line = 0; else if(line >= max_line) line = max_line - 1;
      offset = line - current_line; //if offset pushes line beyond boundaries, reduce it
      var main_image = $("#main-image img");
      var image_pos = main_image.offset();
      var line_pos = image_pos;
      var line_offset = main_image.height() * line_positions[line] / 10000;
      line_pos.top += line_offset;
      var highlight_pos = line_pos;
      highlight_pos.top -= $("#image_highlight").height() / 2;
      //move highlight
      $("#image_highlight").offset(highlight_pos);
      //scroll to center highlight
      var scroll_top = $('#context-image-top').height() +
                         line_offset - $('#images').height() / 2;
      $("#images").scrollTop(scroll_top);
    }


    function modify_offset(c) {
      offset += c;
      select();
    }

    return {
      modify_offset:modify_offset
    };
  }
  var image_container = image_container_func();


  function text_container_func() {

    var num_lines = 0;
    var current_line = 0;
    var current_token = -1;
    var text_history = [];
    var lines, all_lines;
    var goodwords;
    var validation_sn = 0;
    var validator = "";
    var is_baseline = true;
    var page_id;


    $("#text_container").resizable(
      {handles: "s", minHeight: 100,
       stop: function(event, ui) {
         if(localStorage)
           localStorage["text_container_height"] = ui.size.height;
         select();}});
    if(localStorage && localStorage["text_container_height"]) {
      $("#text_container").height(localStorage["text_container_height"]); }
    $(document).bind("uiwidth",
                     function(ob) {$('#text_container, #editor').width(ob.width); select();});
    $(document).bind("page", new_page);


    function new_page(ob) {
      page_id = ob.page_id;
      var jqxhr_text = jQuery.get(ajax_interface, {projid:projid, pageid:page_id, verb:"get_text"});
      var jqxhr_meta =jQuery.getJSON(ajax_interface, { verb:"get_meta", projid: projid});
      var jqxhr_status = jQuery.get(ajax_interface, {projid:projid, pageid:page_id, verb:"status"});
      function init_callback_factory(_page_id) {
        return function(a_text, a_meta, a_status) {
          if(_page_id != page_id) return;
          goodwords = a_meta[0].goodwords || "";
          validator = a_meta[0].validator || "../cgi-bin/proofing_validator.py";
          current_line = 0;
          current_token = -1;
          is_baseline = (a_status[0] == "submitted") ? false : true;
          var localStorageID = projid + "/" + page_id;
          text_history = [];
          if(localStorage && localStorage[localStorageID]) {
            text_history = JSON.parse(localStorage[localStorageID]);
            if(a_text[0] != text_history[0])
              text_history = [];
          }
          if(text_history.length) refresh();
          else change_text(a_text[0]);
        };
      }
      jQuery.when(jqxhr_text, jqxhr_meta, jqxhr_status)
          .done(init_callback_factory(page_id));
    }


    function select(line) {
      if(num_lines == 0) return;
      var num = line != undefined ? line : current_line;
      if(num < 0) num = 0; else if(num >= num_lines) num = num_lines - 1;
      //remove 'current' class from span and line whenever line is changed
      if(num != current_line) {
        current_token = -1;
        $('div.current_line span.current').removeClass("current");
        $("div.current_line").removeClass("current_line");
        $(document).trigger({type:"linechange", line:num});
        current_line = num;
      }
      var current_line_div = $("div.line").eq(num);
      if(current_line_div.length) {
        current_line_div.addClass("current_line");
        if(current_token != -1) {
          var token_count = current_line_div.children('span').length;
          if(token_count && current_token >= token_count)
            current_token = token_count - 1;
          $('div.current_line span').eq(current_token).addClass("current");
        }
        var scroll_top = current_line_div.position().top +
          $('#text').scrollTop() +
          (current_line_div.height() -  $('#text').height()) / 2;
        $('#text').scrollTop(scroll_top);
      }
    }


    function next_token() {
      var token_count = $('div.current_line span').length;
      if(current_line == num_lines - 1 && current_token >= token_count - 1)
        return;//We're on the last token of the page, so do nothing
      $('div.current_line span.current').removeClass("current");
      current_token++;
      if(current_token == token_count) {
        next();
        current_token = 0;
      }
      $('div.current_line span').eq(current_token).addClass("current");
    }


    function prev_token() {
      if(current_line == 0 && current_token == 0)
        return;//We're on the first token of the page, so do nothing
      $('div.current_line span.current').removeClass("current");
      var token_count = $('div.current_line span').length;
      if(current_token == -1)
        current_token = token_count;
      current_token--;
      if(current_token < 0) {
        prev();
        current_token =  $('div.current_line span').length - 1;
      }
      $('div.current_line span').eq(current_token).addClass("current");
    }


    function find_lines(text) {
      //search for new line characters
      lines = []; all_lines = [];
      if(text.length == 0) return;
      var curr_char;
      var char_pos = 0;
      all_lines.push(0);
      if(text.charAt(0) != "\n") lines.push(0);
      while((curr_char = text.charAt(char_pos))) {
        if(curr_char == "\n") {
          all_lines.push(char_pos + 1);
          if(text.charAt(char_pos + 1) != "\n")
            lines.push(char_pos + 1);
        }
        char_pos++;
      }
    }


    function move(offset) {select(current_line + offset);}
    function next() {move(1);}
    function prev() {move(-1);}


    function edit(pos, element) {
      if(element == undefined && current_token != -1)
        element = $('div.current_line span').get(current_token);
      pos = pos || 0;
      var text = text_history[text_history.length -1];
      var caret_pos = lines[current_line];
      //calculate equivalent line including blank lines
      var line = 0;
      while(line < all_lines.length){
        if(all_lines[line] >= caret_pos) break;
        line++;
        }
      $('#text').css('display', 'none');
      if(element == undefined) {
        caret_pos += Math.round(($('div.current_line').text().length -
                                 $('div.current_line div.linenum').text().length) * pos);
      }
      else {
        caret_pos += Math.round($(element).text().length * pos);
        while((element = element.previousSibling)) {
          if(element.className != "linenum")
            caret_pos += $(element).text().length;
        }
      }
      activate_editor(text, caret_pos, line, all_lines.length);
    }


    function activate_editor(text, caret_pos, caret_line, total_lines) {
      var ta = $('#editor textarea').get(0);
      ta.removeAttribute('readonly');
      ta.value = text;
      $('#editor').css('display', 'block');
      $(document).trigger({type:"mode", mode:"editor"});
      //I feel so dirty... have to browser sniff for Opera because it includes newline
      //characters in the count for the caret
      if(navigator.userAgent.toLowerCase().match(/opera/)) {
        caret_pos += caret_line;
      }
      //set caret position either with setSelectionRange or createTextRange as available
      if(ta.setSelectionRange)
        ta.setSelectionRange(caret_pos, caret_pos);
      else if(ta.createTextRange) {//IE
        var range = ta.createTextRange();
        range.collapse(true);
        range.moveEnd('character', caret_pos);
        range.moveStart('character', caret_pos);
        range.select();
      }
      //set scroll position
      var row_height = ta.scrollHeight / total_lines;
      ta.scrollTop = caret_line * row_height - (ta.clientHeight - row_height)/ 2;
      //set focus to the control
      ta.focus();
    }


    function deactivate_editor() {
      var ta = $('#editor textarea').get(0);
      ta.blur();
      ta.setAttribute('readonly', 'readonly');
      $('#editor').css('display', 'none');
      $(document).trigger({type:"mode", mode:"normal"});
      change_text(ta.value);
    }


    function local_validate(text) {
      var lines = [];
      var c;
      var text_ob = $("<div id='text'/>");
      // text_ob.empty();
      if(text.length > 0) {
        for(c = 0; c < all_lines.length - 1; c++) {
          lines[c] = text.slice(all_lines[c], all_lines[c + 1] - 1);
        }
        lines[all_lines.length - 1] = text.slice(all_lines[all_lines.length - 1], text.length);
        for(c = 0; c < lines.length; c++) {
          if(lines[c].length)
            text_ob.append($("<div class='line'/>").text(lines[c]));
          else
            text_ob.append("<div class='blank'/>");
        }
        num_lines = all_lines.length;
      }
      else {
        num_lines = 0;
        text_ob.append("<div class='blank_page'>Blank Page</div>");
      }
      $('#text').replaceWith(text_ob);
      select();
    }


    function change_text(text) {
      $('#text').css('display', 'block');//we may have hidden when showing editor
      text = text.replace(/[^\S\n]+\n/g, "\n");//strip EOL whitespace
      text = text.replace(/\s+$/, ""); //strip EOS whitespace
      text = text.replace(/^\n+\n/, "\n"); //ensure at most one blank line at start of text
      text = text.replace(/\n+\n/g, "\n\n"); //ensure at most one blank line elsewhere
      text = text.replace(/[ \t]+/g, " ");//collapse space and tab sequences to a single space
      if(text_history.length && text == text_history[text_history.length - 1]) {
        select();//safari loses position
        return; //if there is no change, there is nothing to do
      }
      text_history.push(text);
      if(localStorage && text_history.length > 1) {
        var localStorageID = projid + "/" + page_id;
        localStorage[localStorageID] = JSON.stringify(text_history);
      }
      refresh();
    }


    function refresh(skip_validate) {
      if(text_history.length == 0) return;
      var text = text_history[text_history.length - 1];
      find_lines(text);
      if(text_history.length == 1 && is_baseline == false) {
        $(document).trigger({type:"status", status:"clean"});
      }
      else {
        $(document).trigger({type:"status", status:"dirty"});
        }
      if(! skip_validate) {
        local_validate(text);
        if(text.length > 0) {
          jQuery.get(validator,
                     {projid: projid, page_id: page_id, text: text, serial: ++validation_sn, goodwords: goodwords},
                     validator_callback, "html");
        }
      }
      $('#text').focus();
    }


    function validator_callback(response_text, text_status) {
      var current_sn = "<!--" + validation_sn + "-->";
      if(response_text.slice(0, current_sn.length) != current_sn)
        return;//out of sequence validation detected -- don't process it
      $('#text').replaceWith(response_text);
      $('#text').attr("class", "ui-widget-content ui-corner-all");//restore classes
      $('#text div').prepend(function(index, html) {
                               return "<div class='linenum'>" + (index + 1) + "</div>";
                             });
      num_lines = $('#text div.line').length;
      $('span.note').replaceWith(
        function() {
          return $("<img src='../images/postit.png' alt=''/>").attr("title", $(this).text());
        });
      select();
    }


    function add_blank_line() {
      var text = text_history[text_history.length - 1];
      if(text.length == 0) {
        change_text("\n");
        return;
      }
      var pos = lines[current_line];
      text = text.slice(0, pos) + "\n" + text.slice(pos);
      change_text(text);
    }


    function undo() {
      if(text_history.length > 1) {
        text_history.pop();
        if(text_history.length == 1) {
          var localStorageID = projid + "/" + page_id;
          localStorage.removeItem(localStorageID);
        }
        refresh();
      }
    }


    function submit(proj_id) {
      if(!page_id) return;
      jQuery.post(
        ajax_interface,
        {verb:"save", projid: projid, pageid: page_id,
         text:text_history[text_history.length - 1]},
        function(ob) {
          if(ob == "OK") {
            text_history = [text_history[text_history.length - 1]];
            if(localStorage) {
              var localStorageID = projid + "/" + page_id;
              localStorage.removeItem(localStorageID);
            }
            is_baseline = false;
            refresh(true);
          }
          else {
            alert("Submit failed. Please try again.");
          }
        });
    }

    return {
      select: select,
      move: move,
      next: next,
      prev: prev,
      edit: edit,
      end_edit: deactivate_editor,
      undo: undo,
      change_text: change_text,
      next_token: next_token,
      prev_token: prev_token,
      submit: submit,
      focus: function() {$('#text_container').focus();},
      toggle_punc_hl: function() {$('#text_container').toggleClass("nohl");}
    };
  }
  var text_container = text_container_func();


  (function keyhandler() {

    $(document).bind(
      "mode",
      function(ob) {
        $(document).unbind('keydown');
        if(ob.mode == "editor") {
          $(document).keydown(editor_keydown_handler);
        }
        else if(ob.mode == "normal") {
          $(document).keydown(default_keydown_handler);
        }
      });


    function default_keydown_handler(event) {
      // console.log("event.which: " + event.which + ", event.keyCode: " + event.keyCode + ", event.shiftKey: " + event.shiftKey);
      if(event.which == 74 || event.which == 40) { //j or down arrow
        if(event.shiftKey)
          image_container.modify_offset(1);
        else
          text_container.next();
        event.preventDefault();
        event.stopPropagation();//prevent up arrow scrolling focused pane
      }
      else if(event.which == 75 || event.which == 38) { //k or up arrow
        if(event.shiftKey)
          image_container.modify_offset(-1);
        else
          text_container.prev();
        event.preventDefault();
        event.stopPropagation();//prevent down arrow scrolling focused pane
      }
      else if(event.which == 69 || event.which == 73) { //e or i = start editor
        text_container.edit(0);
        event.preventDefault(); //prevent keystroke reaching editor
        event.stopPropagation();
      }
      else if(event.which == 76 || event.which == 32 || event.which == 39) {//l or space bar or right arrow
        text_container.next_token();
        event.preventDefault();
        event.stopPropagation();//prevent space bar and right arrow scrolling focused pane
      }
      else if(event.which == 72 || event.which == 37) {//h or left arrow
        text_container.prev_token();
        event.preventDefault();
        event.stopPropagation();//prevent left arrow scrolling focused pane
      }
      else if(event.which == 85  || event.which == 36) { //u or home
        text_container.select(0);
        event.preventDefault();
        event.stopPropagation();//prevent home button scrolling focused pane
        }
      else if(event.which == 13) {//Enter - add a blank line
        text_container.add_blank_line();
        event.preventDefault();
      }
      else if(event.which == 79) {//o - cursor at end of line
        text_container.edit(1);
        event.preventDefault(); //prevent keystroke reaching editor
        event.stopPropagation();
      }
      else if(event.which == 90) {//z - undo 1 edit
        text_container.undo();
        }
      else if(event.which == 80) {//p - pages
        page_picker.show();
      }
      else if(event.which == 83) {//s - submit
        text_container.submit();
      }
    }


    function editor_keydown_handler(event) {
      if(event.which == 27) {//esc
        text_container.end_edit();
        event.preventDefault(); //cancel default action of ESC as it kills AJAX requests
      }
    }
  })();


  (function command_bar() {
    $(document).bind("uiwidth",
                    function(ob) {$("#control_bar").width(ob.width);});
    $("#change_page, #submit, #reserve, #close_editor, #open_editor").button();
    $('#change_page').click(function(){page_picker.show();});
    $('#submit').click(function(){text_container.submit();});
    $('#open_editor').click(function() {text_container.edit(0);});
    $('#close_editor').click(text_container.end_edit);
    $('#hl-punc').attr('checked', true).change(text_container.toggle_punc_hl);
    $('#hl-punc, #submit, #close_editor').focus(text_container.focus);

    $(document).bind(
      "mode",
      function(ob) {
        if(ob.mode == "editor") {
          $('#control_bar').addClass("editor");
        }
        else {
          $('#control_bar').removeClass("editor");
        }
      });

    $(document).bind(
      "status",
      function(ob) {
        $('#submit').button(
          "option", "disabled",
          (ob.status == "clean") ? true : false);
      });
  })();


  function pagepicker_func() {

    var listing_sn = 0;
    $("#tabs").tabs();
    $("#pagepicker").dialog(
      {autoOpen: false, modal:true, width:500, height:600, position:['center', 50],
       close: function() {$(document).trigger({type:"mode", mode:"normal"});}});


    $('#reserve').click(
      function(ob){
        jQuery.post(ajax_interface,
                    {verb:"reserve", projid: projid},
                    function(ob) {
                      refresh();
                      if(ob == "COMPLETE")
                        alert("Proofing complete.");});
      $('#reserve').button("disable");
    });


    $('#pagepicker').click(
      function(event) {
        event.preventDefault();
        var href = $(event.target).attr('href');
        if(href) {
          $('#pagepicker').dialog('close');
          $(document).trigger({type:"page", page_id:href});
        }
      });


    function refresh() {
      listing_sn++;
      function callback_factory(_listing_sn) {
        return function(ob, status) {
          if(_listing_sn == listing_sn) {
            $('#res_list').replaceWith($("<div id='res_list'/>").append(build_table(ob[0])));
            $('#res_tab_hdg').text("Reserved (" + ob[0].length + ")");
            $('#diff_list').replaceWith($("<div id='diff_list'/>").append(build_table(ob[1])));
            $('#diffs_tab_hdg').text("Diffs (" + ob[1].length + ")");
            $('#done_list').replaceWith($("<div id='done_list'/>").append(build_table(ob[2])));
            $('#done_tab_hdg').text("Done (" + ob[2].length + ")");
            $('#res_list a:first').focus();
            $('#reserve').button("enable");
          }
        };
      }
      jQuery.getJSON(ajax_interface,
        {verb:"list",  projid: projid}, callback_factory(listing_sn));
    }


    function show() {
      $(document).trigger({type:"mode", mode:"picker"});
      $('#pagepicker').dialog('open');
      refresh();
    }


    function build_table(listing) {
        var content = ($("<table/>"));
        for(var c = 0; c < listing.length; c++) {
            content.append($("<tr><td><a href='" +
                             listing[c][0] + "'>" +
                             listing[c][0] + "</a></td><td>" +
                             listing[c][1] + "</td></tr>"));
        }
        return content;
    }

    return {
      show: show
      };
    }
    var page_picker = pagepicker_func();


  (function diffs() {
     var page_id;
     $(document).bind(
       "uiwidth",
       function(ob) {$("#diffs").width(ob.width);});
     $(document).bind(
       "page",
       function(ob) {page_id = ob.page_id; $('#diffs').empty().css("display", "none");});
     $(document).bind(
       "status",
       function(ob) {
         if(ob.status == "clean")
           $('#diffs').load(
             diff_provider, {projid:projid, pageid:page_id},
             function() {
               $("#diffs").accordion("destroy").css("display", "none");
               if($("#diffs h3").length) {
                 $("#diffs").accordion({autoHeight: false, collapsible: true});
               }
               $('#diffs').css("display", "block");});});
  })();


  //Initialise proofreader
  init();
  };




