jQuery(proofreader);
jQuery.ajaxSetup({'cache': false});

function proofreader() {

  var ajax_interface = "../cgi-bin/command.py";
  var projid = "";
  var task = "proof";
  var page_id = "";

  //extract projid and task from URL
  var url_param_strings = location.search.substring(1).split("&");
  for(var c = 0; c < url_param_strings.length; c++) {
    var pos = url_param_strings[c].indexOf("=");
    if(pos == -1) continue;
    var name = url_param_strings[c].substring(0, pos);
    if(name == "projid")  {
      projid = decodeURIComponent(url_param_strings[c].substring(pos + 1));
    }
    else if(name == "task") {
      task = decodeURIComponent(url_param_strings[c].substring(pos + 1));
    }
  }

  //insert title and guidelines link
  function init_callback(ob, status) {
    $('#title').text(ob[0]);
    $("#project_link").attr("href", ob[1]);
  }
  jQuery.getJSON(ajax_interface, { verb:"get", task: "init", projid: projid}, init_callback);


  //set up jQuery ui
  var ui_width = 800;
  if(localStorage && localStorage["ui_width"]) {
    ui_width = localStorage["ui_width"];
    $("#spacer, #title_bar, #image_container, #text_container, #control_bar, #editor, #diffs").width(ui_width);
  }


  function slide(event, ui) {
    $("#spacer, #title_bar, #image_container, #text_container, #control_bar, #editor, #diffs").width(ui.value);
      image_container.select();
      text_container.select();
  }

  $("#slider").slider({ value: ui_width,
                        min: 400,
                        max: 1500,
                        step: 25,
                        slide: slide,
                        stop: function(event, ui) {
                          if(localStorage)
                              localStorage["ui_width"] = ui.value;}});

  $("#spacer").resizable({handles: "s",
                          minHeight: 16,
                          stop: function(event, ui) {
                            if(localStorage)
                              localStorage["spacer_height"] =
                                ui.size.height;}});
  if(localStorage && localStorage["spacer_height"]) {
    $("#spacer").height(localStorage["spacer_height"]); }

  $("#change_page, #submit, #reserve, #close_editor").button();
  $("#close_interface").button({icons:{primary: "ui-icon-closethick"}, text:false});
  $("#tabs").tabs();

  //open all menu_bar links in new windows
  $('#menu_bar > a').click(function(event) {
                           window.open($(this).attr('href'));
                           event.preventDefault();
                         });


  function image_container_func() {

    var current_line;
    var max_line =  0;
    var line_positions;
    var loaded_images;

    $("#image_container").resizable({handles: "s",
                                    minHeight: 100,
                                    stop:
                                    function(event, ui) {
                                      if(localStorage)
                                        localStorage["image_container_height"] =
                                          ui.size.height;
                                      select();
                                      }});
    if(localStorage && localStorage["image_container_height"]) {
      $("#image_container").height(localStorage["image_container_height"]); }


    function load_image(url, pos) {
      url = url || "../images/blank.png";
      var img = $("<img />").attr({'src': url, 'alt': pos});
      if (img.get(0).complete || img.get(0).readyState === 4) {
        image_load_handler({currentTarget: img.get(0)});
      }
      else {
        img.load(image_load_handler);
      }
    }


    function image_load_handler(event) {
      var target = event.currentTarget;
      var pos = target.getAttribute('alt');
      $('#image_container img').eq(pos).replaceWith(target);
      select();
    }


    function init(_images, _line_positions) {
      line_positions = _line_positions.length ? _line_positions : [1000];
      max_line = line_positions.length;
      loaded_images = 0;
      current_line = 0;
      $('#image_container').addClass('wait');
      load_image(_images[1], 1);
      load_image(_images[0], 0);
      load_image(_images[2], 2);
    }


    function select(_line) {
      var line = _line != undefined ? _line : current_line;
      if(line < 0) line = 0; else if(line >= max_line) line = max_line - 1;
      var offset = line - current_line;
      current_line = line;
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
      return offset;
    }


    function click(event) {
      if(event.target.tagName == "IMG") {
        event.offsetY= event.offsetY || event.pageY  - $(event.target).offset().top;
        var line_index = event.offsetY * 10000 / $(event.target).height();
        var line_diff = 10000;//Math.abs(line_positions[c] - line_index);
        for(var c = 0; c < line_positions.length; c++) {
          var new_line_diff = Math.abs(line_positions[c] - line_index);
          if(new_line_diff > line_diff) break;
          line_diff = new_line_diff;
        }
        select(c - 1);
      }
    }
    // $('#image_container').click(click);

    function move(offset) {select(current_line + offset);}
    function next () {move(1);}
    function prev() {move(-1);}

    return {
      init: init,
      select: select,
      move: move,
      next: next,
      prev: prev
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

    $("#text_container").resizable({handles: "s",
                                    minHeight: 100,
                                    stop:
                                    function(event, ui) {
                                      if(localStorage)
                                        localStorage["text_container_height"] =
                                          ui.size.height;
                                      select();
                                      }});
    if(localStorage && localStorage["text_container_height"]) {
      $("#text_container").height(localStorage["text_container_height"]); }


    function init(text, _goodwords, _validator, _is_baseline) {
      goodwords = _goodwords || "";
      validator = _validator;
      is_baseline = _is_baseline;
      current_line = 0;
      current_token = -1;
      var localStorageID = projid + "/" + page_id;
      text_history = [];
      if(localStorage && localStorage[localStorageID]) {
        text_history = JSON.parse(localStorage[localStorageID]);
        if(text != text_history[0])
          text_history = [];
        }
      if(text_history.length) {
        refresh();
      }
      else {
        change_text(text);
      }
    }


    function select(line) {
      var num = line != undefined ? line : current_line;
      if(num < 0) num = 0; else if(num >= num_lines) num = num_lines - 1;
      var offset = line - current_line;
      //remove 'current' class from span and line whenever line is changed
      if(num != current_line) {
        current_token = -1;
        $('div.current_line span.current').removeClass("current");
        $("div.current_line").removeClass("current_line");
      }
      current_line = num;
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
      return offset;
    }


    function next_token() {
      var token_count = $('div.current_line span').length;
      if(current_line == num_lines - 1 && current_token >= token_count - 1)
        return;//We're on the last token of the page, so do nothing
      $('div.current_line span.current').removeClass("current");
      current_token++;
      if(current_token == token_count) {
        next();
        image_container.next();
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
        image_container.prev();
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
      editor.activate(text, caret_pos, line, all_lines.length);
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
        $('#status').removeClass("warn").text("Submitted");
        command_bar.enable_submit(false);
        $('#text').focus();
      }
      else {
        $('#status').addClass("warn").text("Not Submitted");
        command_bar.enable_submit(true);
      }
      if(! skip_validate) {
        local_validate(text);
        if(text.length > 0) {
          jQuery.get(validator,
                     {projid: projid, page_id: page_id, text: text, serial: ++validation_sn, goodwords: goodwords},
                     validator_callback, "html");
        }
      }
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


    function get_text() {return text_history[text_history.length - 1];}
    function is_dirty() {return is_baseline || text_history.length > 1;}
    function set_clean(){
      text_history = [text_history[text_history.length - 1]];
      if(localStorage) {
        var localStorageID = projid + "/" + page_id;
        localStorage.removeItem(localStorageID);
      }
      is_baseline = false;
      refresh(true);
    }

    function click(event) {
      //find clicked line
      var line = 0;
      var div = event.target;
      if(div.tagName == "SPAN" || div.tagName == "IMG")
        div = div.parentNode;
      while((div = div.previousSibling)){
        if($(div).hasClass("line")) line++;
      }
      event.target = event.target || event.srcElement;
      if(line == current_line && event.target.nodeName == "SPAN") {
        var pos = (event.clientX - $(event.target).offset().left) / $(event.target).outerWidth();
        edit(pos, event.target);
      }
      else {
        var offset = select(line);
        image_container.move(offset);
      }
    }
    // $('#text_container').click(click);


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


    return {
      init: init,
      select: select,
      move: move,
      next: next,
      prev: prev,
      edit: edit,
      undo: undo,
      change_text: change_text,
      get_text: get_text,
      is_dirty: is_dirty,
      set_clean: set_clean,
      add_blank_line: add_blank_line,
      next_token: next_token,
      prev_token: prev_token
    };
  }
  var text_container = text_container_func();


  function editor_func() {
    //easier to handle raw elememnt for textarea
    var ta = $('#editor textarea').get(0);


    function activate(text, caret_pos, caret_line, total_lines) {
      ta.removeAttribute('readonly');
      ta.value = text;
      $('#editor').css('display', 'block');
      command_bar.editor_mode(true);
      keyhandler.editor();
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


    function deactivate() {
      ta.blur();
      ta.setAttribute('readonly', 'readonly');
      $('#editor').css('display', 'none');
      command_bar.editor_mode(false);
      keyhandler.normal();
      text_container.change_text(ta.value);
    }

    return {
      activate: activate,
      deactivate: deactivate
    };
  }
  var editor = editor_func();


  function command_func() {
    var control_data;

    function page_callback(ob, status) {
      //initialise controls
      control_data = ob;
      if(ob[0] != page_id) return; //out of synch callback
      $('#pageid').text(page_id);
      text_container.init(ob[1], ob[4], ob[5], ob[6]);
      image_container.init(ob[2], ob[3]);
      if(ob[6]) {//if baseline
        $('#diffs').css('display', 'none');
        $('#diffs').empty();
      }
      else {
        $('#diffs').css('display', 'none');
        $("#diffs").accordion("destroy");
        $('#diffs').load(ajax_interface, {verb:"diffs", task: task, projid: projid, pageid: page_id}, diffload_callback);
      }
    }

    function diffload_callback(ob, status) {
      if($("#diffs h3").length) {
            $("#diffs").accordion({autoHeight: false, collapsible: true});
      }
      $('#diffs').css('display', 'block');
    }

    function get_page(proj_id, _page_id) {
      page_id = _page_id;
      jQuery.getJSON(ajax_interface, { verb:"get", task: task, projid: proj_id, pageid: page_id}, page_callback);
    }


    function submit(proj_id) {
      if(!page_id) return;
      jQuery.post(ajax_interface,
                  {verb:"save", task:task, projid: proj_id, pageid: page_id, text:text_container.get_text()},
                  submit_callback);
    }


    function submit_callback(ob, status) {
      if(ob == "OK") {
        text_container.set_clean();
        $('#diffs').css('display', 'none');
        $("#diffs").accordion("destroy");
        $('#diffs').load(ajax_interface, {verb:"diffs", task: task, projid: projid, pageid: page_id}, diffload_callback);
      }
      else {
        $("status").text("Save failed");
      }
    }


    function list(proj_id) {
      page_picker.show();
    }


    function reserve(proj_id) {
      jQuery.post(ajax_interface,
                  {verb:"reserve", task:task, projid: proj_id}, reserve_callback);
    }


    function reserve_callback(ob, status) {
      page_picker.refresh();
      if(ob == "NONE_AVAILABLE") {
        alert("Task \"" + task + "\" has no further pages available to reserve at this time. Please try later.");
      }
      else if(ob == "COMPLETE") {
        alert("Task \"" + task + "\" is complete.");
      }
    }


    return {
      get_page: get_page,
      submit: submit,
      list: list,
      reserve: reserve
    };
  }
  var command = command_func();


  function keyhandler_func()  {

    function set_default() {
      $(document).unbind('keydown');
      $(document).keydown(default_keydown_handler);
    }

    function set_editor() {
      $(document).unbind('keydown');
      $(document).keydown(editor_keydown_handler);
    }

    function set_none() {
      $(document).unbind('keydown');
    }

    function default_keydown_handler(event) {
      // console.log("event.which: " + event.which + ", event.keyCode: " + event.keyCode + ", event.shiftKey: " + event.shiftKey);
      if(event.which == 74 || event.which == 40) { //j or down arrow
        image_container.next();
        if(!event.shiftKey)
          text_container.next();
        event.preventDefault();
        event.stopPropagation();//prevent up arrow scrolling focused pane
      }
      else if(event.which == 78) {//n
        image_container.next();
      }
      else if(event.which == 75 || event.which == 38) { //k or up arrow
        image_container.prev();
        if(!event.shiftKey)
          text_container.prev();
        event.preventDefault();
        event.stopPropagation();//prevent down arrow scrolling focused pane
      }
      else if(event.which == 69 || event.which == 73 || event.which == 27) { //e or i or ESC = start editor
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
        image_container.select(0);
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
        command.list(projid);
      }
      else if(event.which == 83) {//s - submit
        command.submit(projid);
      }
    }

    function editor_keydown_handler(event) {
      if(event.which == 27) {//esc
        editor.deactivate();
        event.preventDefault(); //cancel default action of ESC as it kills AJAX requests
      }
    }

    return {
      normal: set_default,
      editor: set_editor,
      none: set_none
    };
  }
  var keyhandler = keyhandler_func();


  function command_bar_func() {

    $('#change_page').click(function(){command.list(projid);});
    $('#submit').click(function(){command.submit(projid);});
    $('#close_editor').click(editor.deactivate);
    $('#hl-punc').change(function(eventObject) {
                            $('#text_container').toggleClass("nohl");
                        });
    $('#hl-punc, #submit, #close_editor').focus(function() {
                          $('#text_container').focus();
                        });
    editor_mode(false);


    function editor_mode(bool) {
      if(bool) {
        $('#control_bar').addClass("editor");
      }
      else {
        $('#control_bar').removeClass("editor");
      }
    }


    function enable_submit(bool) {
      $('#submit').button("option", "disabled", !bool);
    }

    return {
      editor_mode: editor_mode,
      enable_submit: enable_submit
    };
  }
  var command_bar = command_bar_func();


  function pagepicker_func() {

    $("#pagepicker").dialog(
      {autoOpen: false,
       modal:true,
       width:500, height:600, position: ['center', 50],
       close: before_close});


    function reserve() {
      command.reserve(projid);
    }
    $('#reserve').click(reserve);


    function click(event) {
      event.preventDefault();
      var href = $(event.target).attr('href');
      if(href) {
        $('#pagepicker').dialog('close');
        command.get_page(projid, href);
      }
    }
    $('#pagepicker').click(click);


    function refresh() {
      jQuery.getJSON(ajax_interface,
        {verb:"list", task: task, type: "res", projid: projid}, list_callback);
      jQuery.getJSON(ajax_interface,
        {verb:"list", task: task, type: "done", projid: projid}, list_callback);
    }


    function show() {
      keyhandler.none();
      $('#pagepicker').dialog('open');
      refresh();
    }


    function before_close() {
      keyhandler.normal();
    }


    function list_callback(ob, status) {
      var list_type = ob[0];
      var listing = ob[1];
      var content;
      if(listing.length > 0) {
        content = ($("<table/>"));
        for(var c = 0; c < listing.length; c++) {
          var class_string = "";
          if(listing[c][2])
            class_string = " class='diffs_avbl'";
          content.append($("<tr" + class_string + "><td><a href='" +
                           listing[c][0] + "'>" +
                           listing[c][0] + "</a></td><td>" +
                           listing[c][1] + "</td></tr>"));
        }
      }
      $('#' + list_type).replaceWith($("<div id='" + list_type + "'/>").append(content));
      if(list_type == "res") $('#res a:first').focus();
    }


    return {
      show: show,
      refresh: refresh
      };
    }
    var page_picker = pagepicker_func();

    //Show pagepicker to start
    page_picker.show();
  };




