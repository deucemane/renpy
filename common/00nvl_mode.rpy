# This is an implementation of NVL-mode, which can be used to show
# dialogue in a fullscreen way, like NVL-style games. Multiple lines
# of dialogue are shown on the screen at once, whenever a line of
# dialogue is said by a NVLCharacter. Calling the nvl_clear function
# clears the screen, ensuring that the the next line will appear at
# the top of the screen.
#
# You can also have menus appear on the screen, by running:
#
# init:
#     $ menu = nvl_menu
#
# It's also possible to make the narrator a NVLCharacter, using code like:
#
# init:
#     $ narrator = NVLCharacter(None)
        
##############################################################################
# The implementation of NVL mode lives below this line.

init -1100 python:

    # Styles that are used by nvl mode.
    style.create('nvl_window', 'default')
    style.create('nvl_vbox', 'vbox')
    style.create('nvl_label', 'say_label')
    style.create('nvl_dialogue', 'say_dialogue')
    style.create('nvl_entry', 'default')

    style.create('nvl_menu_window', 'default')
    style.create('nvl_menu_choice', 'default')
    style.create('nvl_menu_choice_chosen', 'nvl_menu_choice')
    style.create('nvl_menu_choice_button', 'default')
    style.create('nvl_menu_choice_chosen_button', 'nvl_menu_choice_button')

    # Set up nvl mode styles.
    style.nvl_label.minwidth = 150
    style.nvl_label.text_align = 1.0

    style.nvl_window.background = "#0008"
    style.nvl_window.yfill = True
    style.nvl_window.xfill = True
    style.nvl_window.xpadding = 20
    style.nvl_window.ypadding = 30

    style.nvl_vbox.box_spacing = 10

    style.nvl_menu_choice.idle_color = "#0ff"
    style.nvl_menu_choice.hover_color = "#ff0"
    style.nvl_menu_choice_button.left_margin = 160
    style.nvl_menu_choice_button.right_margin = 20
    style.nvl_menu_choice_button.xfill = True
    style.nvl_menu_choice_button.hover_background = "#F0F2"

    # nvlmode: The CTC indicator to use when at the end of an NVL page.
    config.nvl_page_ctc = None

    # nvlmode: The position of the CTC indicator used at the end of an NVL page.
    config.nvl_page_ctc_position = "nestled"
    
    # A list of arguments that have been passed to nvl_record_show.
    nvl_list = None
    
    def nvl_show_core():

        ui.window(style='nvl_window')
        ui.vbox(style='nvl_vbox')

        rv = None

        for i in nvl_list:
            if not i:
                continue

            who, what, kw = i                
            rv = renpy.show_display_say(who, what, **kw)

        ui.close()
        return rv

    def nvl_show(with_):
        nvl_show_core()
        renpy.with_statement(with_)

    def nvl_hide(with_):
        nvl_show_core()
        renpy.with_statement(None)
        renpy.with_statement(with_)

    def nvl_erase():
        if nvl_list:
            nvl_list.pop()

    # Check to see if one of the next statements is nvl clear.
    def nvl_clear_next():

        # The number of statements forward to look.
        count = 10

        scry = renpy.scry()
        scry = scry.next()

        while count and scry:

            count -= 1
            if scry.nvl_clear:
                return True

            if scry.interacts:
                return False

            scry = scry.next()
        
            
    class NVLCharacter(ADVCharacter):

        def __init__(self, 
                     who=renpy.character.NotSet,
                     kind=None,
                     **properties):
            
            if kind is None:
                kind = store.nvl
            
            if "clear" in properties:
                self.clear = properties.pop("clear")
            else:
                self.clear = kind.clear

            ADVCharacter.__init__(
                self, 
                who,
                kind=kind,
                **properties)

        def do_add(self, who, what):
            if store.nvl_list is None:
                store.nvl_list = [ ]
                
            kwargs = self.show_args.copy()
            kwargs["what_args"] = self.what_args
            kwargs["who_args"] = self.who_args
            kwargs["window_args"] = self.window_args
            
            store.nvl_list.append((who, what, kwargs))

        def do_display(self, who, what, **display_args):
            
            if config.nvl_page_ctc and (self.clear or nvl_clear_next()):
                display_args["ctc"] = config.nvl_page_ctc
                display_args["ctc_position"] = config.nvl_page_ctc_position
            
            renpy.display_say(nvl_show_core,
                              **display_args)
            
        def do_done(self, who, what):
            
            if self.clear:
                nvl_clear()

        def do_extend(self):
            store.nvl_list = store.nvl_list[:-1]
                
    # The default NVLCharacter.
    nvl = NVLCharacter(
        show_say_vbox_properties={ 'box_layout' : 'horizontal' },
        who_style='nvl_label',
        what_style='nvl_dialogue',
        window_style='nvl_entry',
        type='nvl',
        clear=False,
        kind=adv)

                
    def nvl_clear():
        store.nvl_list = [ ]

    # Run clear at the start of the game.
    config.start_callbacks.append(nvl_clear)

    def nvl_menu(items):

        # Clear out the previous scene list, as we will need to redraw
        # it.
        renpy.with_statement(None)

        if nvl_list is None:
            store.nvl_list = [ ]

        ui.window(style='nvl_window')
        ui.vbox(style='nvl_vbox')

        for i in nvl_list:
            if not i:
                continue

            who, what, kw = i            
            rv = renpy.show_display_say(who, what, **kw)

        renpy.display_menu(items, interact=False,
                           window_style='nvl_menu_window',
                           choice_style='nvl_menu_choice',
                           choice_chosen_style='nvl_menu_choice_chosen',
                           choice_button_style='nvl_menu_choice_button',
                           choice_chosen_button_style='nvl_menu_choice_chosen_button',
                           )

        ui.close()

        roll_forward = renpy.roll_forward_info()

        rv = ui.interact(roll_forward=roll_forward)
        renpy.checkpoint(rv)

        return rv

    config.nvl_adv_transition = None
    config.adv_nvl_transition = None

init 1140 python:

    if config.nvl_adv_transition or config.adv_nvl_transition:

        def _nvl_adv_callback(event, interact, type, **kwargs):
        
            if event != "begin" or not interact or renpy.get_transition():
                return 
            
            old_type = renpy.last_interact_type()

            if old_type == "say" and type == "nvl":
                # We have an extra line in the nvl_list as we do this. So
                # take it out for the duration of the nvl_show.
                old_nvl_list = store.nvl_list
                store.nvl_list = old_nvl_list[:-1]
                nvl_show(config.adv_nvl_transition)
                store.nvl_list = old_nvl_list
            elif old_type == "nvl" and type == "say":
                nvl_hide(config.nvl_adv_transition)

        config.all_character_callbacks.insert(0, _nvl_adv_callback)

    
python early hide:

    def parse_nvl_show_hide(l):
        rv = l.simple_expression()
        if rv is None:
            renpy.error('expected simple expression')

        if not l.eol():
            renpy.error('expected end of line')

        return rv
            
    def lint_nvl_show_hide(trans):
        _try_eval(trans, 'transition')

    def execute_nvl_show(trans):
        nvl_show(eval(trans))

    def execute_nvl_hide(trans):
        nvl_hide(eval(trans))

    renpy.statements.register("nvl show",
                              parse=parse_nvl_show_hide,
                              execute=execute_nvl_show,
                              lint=lint_nvl_show_hide)

    renpy.statements.register("nvl hide",
                              parse=parse_nvl_show_hide,
                              execute=execute_nvl_hide,
                              lint=lint_nvl_show_hide)

    def parse_nvl_clear(l):
        if not l.eol():
            renpy.error('expected end of line')

        return None

    def execute_nvl_clear(parse):
        nvl_clear()

    def scry_nvl_clear(parse, scry):
        scry.nvl_clear = True
        
    renpy.statements.register('nvl clear',
                              parse=parse_nvl_clear,
                              execute=execute_nvl_clear,
                              scry=scry_nvl_clear)


    
