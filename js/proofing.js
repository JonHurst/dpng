jQuery(proofreader);
jQuery.ajaxSetup({'cache': false});

function proofreader() {

  var cgi_path = "../cgi-bin/";
  var projid = $('body').attr('id');//projid id is body tag id for now

  function image_container_func() {

    var current_line;
    var max_line =  0;
    var line_positions;
    var loaded_images;


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
      loaded_images++;
      if(loaded_images == 3) {
        $('#image_container').removeClass('wait');
        select();
      }
    }


    function init(_images, _line_positions) {
      line_positions = _line_positions.length ? _line_positions : [1000];
      max_line = line_positions.length;
      loaded_images = 0;
      current_line = 0;
      $('#image_container').addClass('wait');
      for(var c = 0; c < 3; c++)
        load_image(_images[c], c);
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
                         line_offset - $('#image_container').height() / 2;
      $("#image_container").scrollTop(scroll_top);
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
    $('#image_container').click(click);

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
    var text_history = [];
    var text_dirty;
    var lines, all_lines;
    var goodwords;

    function init(text, _goodwords) {
      goodwords = _goodwords || "";
      current_line = 0;
      text_container.change_text(text);
      text_dirty = false;
      $('#status').text("Unchanged");
    }


    function select(line) {
      var num = line != undefined ? line : current_line;
      if(num < 0) num = 0; else if(num >= num_lines) num = num_lines - 1;
      var offset = line - current_line;
      current_line = num;
      $("div.current_line").removeClass("current_line");
      var current_line_div = $("div.line").eq(num);
      if(current_line_div.length) {
        current_line_div.addClass("current_line");
        var scroll_top = current_line_div.position().top +
          (current_line_div.height() -  $('#text_container').height()) / 2;
        $('#text_container').scrollTop(scroll_top);
      }
      return offset;
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


    function edit() {
      var text = text_history[text_history.length -1];
      var caret_pos = lines[current_line];
      $('#text_container').css('display', 'none');
      editor.activate(text, caret_pos);
    }


    function local_validate(text) {
      var lines = [];
      var c;
      var text_ob = $("<div id='text'/>");
      text_ob.empty();
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
      $('#text').replaceWith(text_ob);
      select();
    }


    function change_text(text) {
      $('#text_container').css('display', 'block');//we may have hidden when showing editor
      text = text.replace(/[^\S\n]+\n/g, "\n");//strip EOL whitespace
      text = text.replace(/\s+$/, ""); //strip EOS whitespace
      //TODO: The following may need to be disabled for formatting
      text = text.replace(/^\n+\n/, "\n"); //ensure at most one blank line at start of text
      text = text.replace(/\n+\n/g, "\n\n"); //ensure at most one blank line elsewhere
      if(text_history.length && text == text_history[text_history.length - 1]) {
        select();//safari loses position
        return; //if there is no change, there is nothing to do
      }
      text_history.push(text);
      find_lines(text);
      if(text_history.length > 1) {
        text_dirty = true;
        $('#status').text("Not saved");
      }
      local_validate(text);
      // console.log(text_history);
      $('#text_container').load(cgi_path + "proofing_validator.py", {"text": text, "goodwords": goodwords}, validator_callback);
    }


    function validator_callback(response_text, text_status) {
      num_lines = $('#text div.line').length;
      $('span.note').replaceWith(
        function() {
          return $("<img src='../images/postit.png' alt=''/>").attr("title", $(this).text());
        });
      select();
    }


    function get_text() {return text_history[text_history.length - 1];}
    function is_dirty() {return text_dirty;}
    function set_clean(){text_dirty = false; $('#status').text("Saved");}

    function click(event) {
      //find clicked line
      var line = 0;
      var div = event.target;
      if(div.tagName == "SPAN" || div.tagName == "IMG")
        div = div.parentNode;
      while((div = div.previousSibling)){
        if($(div).hasClass("line")) line++;
      }
      if(line == current_line)
        edit();
      else {
        var offset = select(line);
        image_container.move(offset);
      }
    }
    $('#text_container').click(click);

    return {
      init: init,
      select: select,
      move: move,
      next: next,
      prev: prev,
      edit: edit,
      change_text: change_text,
      get_text: get_text,
      is_dirty: is_dirty,
      set_clean: set_clean
    };
  }
  var text_container = text_container_func();


  function editor_func() {
    //easier to handle raw elememnt for textarea
    var ta = $('#editor textarea').get(0);


    function activate(text, caret_pos) {
      ta.removeAttribute('readonly');
      ta.value = text;
      $('#editor').css('display', 'block');
      command_bar.editor_mode(true);
      keyhandler.editor();
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
      var total_lines = 0, caret_line = 0;
      var char_pos = 0, curr_char;
      while((curr_char = text.charAt(char_pos))) {
        if(curr_char == '\n') {
          total_lines++;
          if(char_pos < caret_pos) caret_line++;
          }
        char_pos++;
      }
      var row_height = ta.scrollHeight / total_lines;
      ta.scrollTop = caret_line * row_height - ta.clientHeight / 2;
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
    var page_id = "";

    function page_callback(ob, status) {
      //initialise controls
      control_data = ob;
      page_id = ob[0];
      $('#title').text(ob[1]);
      $('#pageid').text(page_id);
      text_container.init(ob[2], ob[5]);
      image_container.init(ob[3], ob[4]);
      $('#modal_greyout').css("display", "none");
    }


    function get_page(proj_id, page_id) {
      jQuery.getJSON(cgi_path + "command.py", { verb:"get", projid: proj_id, pageid: page_id}, page_callback);
    }


    function submit(proj_id) {
      jQuery.post(cgi_path + "command.py",
                  {verb:"save", projid: proj_id, pageid: page_id, text:text_container.get_text()},
                  submit_callback);
    }


    function submit_callback(ob, status) {
      if(ob == "OK") {
        text_container.set_clean();
      }
      else {
        $("status").text("Save failed");
      }
    }


    function list(proj_id) {
      if(text_container.is_dirty()) {
        var answer = window.confirm("Page has not been saved. Continue anyway?");
        if(answer == false) return;
      }
      page_picker.show();
    }


    function reserve(proj_id) {
      jQuery.post(cgi_path + "command.py",
                  {verb:"reserve", projid: proj_id}, reserve_callback);
    }


    function reserve_callback(ob, status) {
      page_picker.show();
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
      if(event.which == 74) { //j
        image_container.next();
        if(!event.shiftKey)
          text_container.next();
      }
      else if(event.which == 78) {//n
        image_container.next();
      }
      else if(event.which == 75) { //k
        image_container.prev();
        if(!event.shiftKey)
          text_container.prev();
      }
      else if(event.which == 69 || event.which == 73) { //e = start editor
        text_container.edit();
        event.preventDefault(); //prevent keystroke reaching editor
      }
      else if(event.which == 72) { //h
        text_container.select(0);
        image_container.select(0);
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
    editor_mode(false);

    function enabled(state) {
      if(state) {
        $('#change_page').removeAttr("disabled");
        $('#submit').removeAttr("disabled");
        $('#close_editor').removeAttr("disabled");
      }
      else {
        $('#change_page').attr("disabled", "disabled");
        $('#submit').attr("disabled", "disabled");
        $('#close_editor').attr("disabled", "disabled");
      }
    }

    function editor_mode(bool) {
      if(bool) {
        $('#change_page').css("display", "none");
        $('#submit').css("display", "none");
        $('#close_editor').css("display", "inline");
      }
      else {
        $('#change_page').css("display", "inline");
        $('#submit').css("display", "inline");
        $('#close_editor').css("display", "none");
      }
    }

    return {
      editor_mode: editor_mode,
      enabled: enabled
    };
  }
  var command_bar = command_bar_func();


  function pagepicker_func() {

    function cancel() {
      $('#modal_greyout').css("display", "none");
      hide();
    }
    $('#cancel').click(cancel);


    function click(event) {
      event.preventDefault();
      var href = $(event.target).attr('href');
      if(href) {
        hide();
        keyhandler.normal();
        command.get_page(projid, href);
      }
    }
    $('#pagepicker').click(click);


    function show() {
      $('#modal_greyout').css("display", "block");
      command_bar.enabled(false);
      keyhandler.none();
      $('#pagepicker_tables').load(cgi_path + "command.py",
                                   {verb:"list", projid: projid}, list_callback);
    }

    function hide() {
      $('#pagepicker').css("display", "none");
      command_bar.enabled(true);
    }

    function list_callback(ob, status) {
      $('#pagepicker').css("display", "block");
    }


    return {
      show: show,
      hide: hide
      };
    }
    var page_picker = pagepicker_func();


    //use jQuery ui to make control_container resizable
    function on_control_resize_stop(event, ui) {
      image_container.select();
      text_container.select();
    }
    $('#control_container').resizable({stop: on_control_resize_stop});

    $('#menu_bar a').click(function(event) {
                             console.log($(this).attr('href'));
                             window.open($(this).attr('href'));
                             event.preventDefault();
                             });


    //Reserve pages and start
    command.reserve(projid);
  };




