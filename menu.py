from evennia.utils import evmenu
import wodsystem, time
from evennia.utils.ansi import ANSIString
from evennia.utils import eveditor
from wodsystem import helper
import itertools
from evennia import logger

def set_temp(caller, clear=False, **kwargs):
    if clear:
        try:
            del caller.ndb._menutree.template
        except:
            pass
        try:
            del caller.ndb._menutree.race_template
        except:
            pass
        try:
            del caller.ndb._menutree.headers
        except:
            pass
        try:
            del caller.ndb._menutree.current_data
        except:
            pass
        try:
            caller.ndb._menutree.base_stat = 0
        except:
            pass
        try:
            del caller.ndb._menutree.temp_data
        except:
            pass
        try:
            del caller.ndb._menutree.option_list
        except:
            pass
    else:
        if 'template' in list(kwargs.keys()):
            caller.ndb._menutree.template = kwargs['template']
            caller.ndb._menutree.race_template = helper.get_template_options(caller,kwargs['template'])
            caller.ndb._menutree.headers = kwargs['template']['Headers']
        if 'current_data' in list(kwargs.keys()):
            caller.ndb._menutree.current_data = kwargs['current_data']
        if 'base_stat' in list(kwargs.keys()):
            caller.ndb._menutree.base_stat = kwargs['base_stat']
        if 'option_list' in list(kwargs.keys()):
            caller.ndb._menutree.option_list = kwargs['option_list']
        if not hasattr(caller.ndb._menutree,'temp_data') and 'temp_data' in list(kwargs.keys()):
            caller.ndb._menutree.temp_data = kwargs['temp_data']


def menu_chargen(caller):
    text = "Choose an option"
    options = []
    set_temp(caller, clear=True)
    options.append({"desc": "Edit Race (Currently: |y%s|n) (|RNOTE|n: Set this first.  Changing it will reset your character.)" % (caller.db.cg_info['Race'] if 'Race' in list(caller.db.cg_info.keys()) else 'None'), "goto": "menu_race_choose"})
    options.append({"desc": "Edit Background (Current size: |y%s|n characters)" % len(helper.load_bg(caller)), "goto": "chargen_background"})
    options.append({"desc": "Edit Faction (Currently: |y%s|n)" % (caller.db.cg_info['Faction'] if 'Faction' in list(caller.db.cg_info.keys()) else 'None'), "goto": "menu_faction_choose"})
    attr_points = helper.get_cg_points_spent(caller.db.cg_attributes, base_stat=1)
    attr_desc = "Edit Attributes (Current points spent: |y%d|n)" % attr_points
    if attr_points:
        caller.db.cg_advantages = helper.calculate_advantages(caller)
        attr_desc += " (|RNOTE|n: This will reset all your attributes.)"
    options.append({"desc": attr_desc, "goto": ("menu_set_stats", {"template": wodsystem.ATTRIBUTE_LIST,
                                                                   "pools": caller.db.cg_creationpools['Attributes'],
                                                                   "current_data": 'cg_attributes',
                                                                   "base_stat": 1}
                                                )
                    }
                   )
    if caller.chargenfinished(segment='Attributes'):
        skill_points = helper.get_cg_points_spent(caller.db.cg_skills)
        skill_desc = "Edit Skills (Current points spent: |y%d|n)" % skill_points
        if skill_points:
            skill_desc += " (|RNOTE|n: This will reset all your skills.)"
        options.append({"desc": skill_desc, "goto": ("menu_set_stats", {"template": wodsystem.SKILL_LIST,
                                                                        "pools": caller.db.cg_creationpools['Skills'],
                                                                        "current_data": 'cg_skills',
                                                                        "base_stat": 0}
                                                            )
                        }
                       )
    if caller.chargenfinished(segment='Attributes') and caller.chargenfinished(segment='Skills'):
        merit_points = helper.get_cg_points_spent(caller.db.cg_merits)
        merit_desc = "Edit Merits (Current points spent: |y%d|n)" % merit_points
        options.append({"desc": merit_desc, "goto": ("menu_set_merits", {"template": wodsystem.MERIT_LIST,
                                                                        "pools": caller.db.cg_creationpools['Merits'],
                                                                        "current_data": 'cg_merits'}
                                                     )
                        }
                       )
        options.append({"key": ("Exit", "Quit", "q"), "desc": "Exit Chargen", "goto": "menu_exit_chargen"})
    return text, options

def menu_exit_chargen(caller):
    caller.msg("Once this project is finished, you would now confirm that you're happy with your character, and save it. However, for now, we just auto-save and leave chargen avaialble.")
    caller.msg("\n\nYou may once again use commands.")

def menu_faction_choose(caller):
    text = helper.wod_header("Choose a Faction")
    current_faction = caller.db.cg_info['Faction'] if 'Faction' in list(caller.db.cg_info.keys()) else 'None'
    text += "\n" + ANSIString("|nYour current Faction is: |w%s" % current_faction).center(width=78, fillchar=" ")
    text += "\n" + helper.wod_header() + "\n\n Choose a faction:"
    factions = helper.get_template_options(caller, wodsystem.FACTIONS_LIST)
    options = []
    if current_faction != 'None':
        options.append({"key": "None", "desc": "Do not change.", "goto": (_set_info, {"name": "Faction", "info": current_faction})})
    for faction in factions:
        options.append({"key": faction, "desc": "Set to '%s'." % faction, "goto": (_set_info, {"name": "Faction", "info": faction})})
    if not caller.chargenfinished():
        options.append(
            {"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Return to Chargen Main Menu", "goto": "menu_chargen"})
    else:
        options.append({"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Exit the Menu", "goto": "menu_exit_chargen"})

    return text, options


def menu_race_choose(caller):
    text = helper.wod_header("Choose a Race")
    current_race = caller.db.cg_info['Race'] if 'Race' in list(caller.db.cg_info.keys()) else 'Mortal'
    text += "\n" + ANSIString("|nYour current Race is: |w%s" % current_race).center(width=78, fillchar=" ")
    text += "\n" + helper.wod_header() + "\n\n Choose a race:"
    races = wodsystem.RACE_LIST
    options = []
    if current_race != 'None':
        options.append({"key": "None", "desc": "Do not change.", "goto": (_set_race, {"name": "Race", "info": current_race})})
    for race in races:
        options.append(
            {"key": race, "desc": "Set to '%s'." % race, "goto": (_set_race, {"name": "Race", "info": race})}
        )
    if not caller.chargenfinished():
        options.append(
            {"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Return to Chargen Main Menu", "goto": "menu_chargen"})
    else:
        options.append({"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Exit the Menu", "goto": "menu_exit_chargen"})
    return text, options


def chargen_background(caller, rawstring, **kwargs):
    helper.background_edit(caller)
    return

def _set_info(caller, raw_string, **kwargs):
    attribute = kwargs.get("name", "Error")
    value = kwargs.get("info", "Error")
    caller.db.cg_info[attribute] = value
    logger.log_file('%s set %s to %s' % (caller.name, attribute, value))
    return ''


def _set_race(caller, raw_string, **kwargs):
    race = kwargs.get("info", None)
    if race:
        caller.ndb.race = race
        helper.init_object(caller)
    return ''


def menu_set_merits(caller, raw_string, **kwargs):
    set_temp(caller, **kwargs)
    mt = caller.ndb._menutree
    if 'pools' in list(kwargs.keys()):
        maxpoints = kwargs['pools']
    else:
        if hasattr(caller.ndb._menutree,'option_list'):
            maxpoints = mt.option_list['Merits']['MaxPoints']
        else:
            maxpoints = 0
    points_left = maxpoints - helper.get_cg_points_spent(caller.db.cg_merits)
    set_temp(caller, option_list={'Merits': {'Points': points_left, 'MaxPoints': maxpoints}})
    if points_left:
        caller.chargenfinished(segment='Merits', value=False)
    else:
        caller.chargenfinished(segment='Merits', value=True)
    options = []
    text = ''
    if mt.race_template:
        set_temp(caller, temp_data=dict(caller.db.cg_merits))
        text = helper.get_cg_data(mt.template, mt.headers, mt.temp_data, datatype='merits', caller=caller, points_left=points_left, for_purchase=True)
        keys = list(mt.race_template.keys())
        for key_dict in mt.headers:
            options.append({"desc": '%s (|y%s points to spend.|n)' % (key_dict, mt.option_list['Merits']['Points']),
                            "goto": ("menu_select_merit", {'Group': key_dict})})
        if not caller.chargenfinished():
            options.append({"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Return to Chargen Main Menu", "goto": "menu_chargen"})
        else:
            options.append({"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Exit the Menu", "goto": "menu_exit_chargen"})
    return text, options


def menu_set_stats(caller, raw_string, **kwargs):
    set_temp(caller, **kwargs)
    mt = caller.ndb._menutree
    options = []
    text = ''
    if mt.race_template:
        temp_data = {}
        for key in list(mt.race_template.keys()):
            temp_data[key] = {}
            for subkey in mt.race_template[key]:
                temp_data[key][subkey] = mt.base_stat
        set_temp(caller, temp_data=temp_data)
        text = helper.get_cg_data(mt.template, mt.headers, mt.temp_data, for_purchase=True, caller=caller)
        keys = list(mt.race_template.keys())
        for p in itertools.permutations(keys):
            option_list = {}
            desc = ''
            for x in range(0, 3):
                perm_dict = {"Points": kwargs['pools'][x], "MaxPoints": kwargs['pools'][x]}
                option_list[p[x]] = perm_dict
                desc += "%s (|y%s|n)" % (p[x], kwargs['pools'][x])
                desc += ", " if x < 2 else ""
            options.append({"desc": desc, "goto": ("menu_select_group", {"option_list": option_list})})
            # text += str(p)
        if not caller.chargenfinished():
            options.append({"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Return to Chargen Main Menu", "goto": "menu_chargen"})
        else:
            options.append({"key": ("Exit", "Quit", "q", "Back", "<"), "desc": "Exit the Menu", "goto": "menu_exit_chargen"})
    return text, options


def get_remaining_points(option_list):
    pointsleft = 0
    for group in list(option_list.keys()):
        pointsleft += option_list[group]['Points']
    return pointsleft


def menu_select_group(caller, raw_string, **kwargs):
    if 'option_list' in list(kwargs.keys()):
        set_temp(caller, option_list=kwargs['option_list'])
    mt = caller.ndb._menutree
    pointsleft = get_remaining_points(mt.option_list)
    text = helper.get_cg_data(mt.template, mt.headers, mt.temp_data, for_purchase=True, caller=caller)
    options = []
    for key_dict in list(mt.option_list.keys()):
        options.append({"desc": '%s (|y%s points to spend.|n)' % (key_dict, mt.option_list[key_dict]['Points']), "goto": ("menu_select_stat", {'Group': key_dict})})
    if pointsleft:
        options.append({"key": (">", "accept", "continue"), "desc": "Accept these stats. |rWARNING|n: You still have |y%d|n unspent points" % pointsleft, "goto": "menu_confirm_accept"})
    else:
        options.append({"key": (">", "accept", "continue"), "desc": "Accept these stats.", "goto": "menu_accept_stats"})
    return text, options


def menu_select_stat(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    text = str(helper.get_cg_data(mt.template, mt.headers, mt.temp_data, highlight_column=kwargs['Group'], for_purchase=True, caller=caller))
    points = mt.option_list[kwargs['Group']]['Points']
    pointsleft = get_remaining_points(mt.option_list)
    text += '\n|y%d|n points left to spend in this group.' % points
    options = []
    for stat in mt.race_template[kwargs['Group']]:
        options.append({"desc": stat, "goto": ("menu_adjust_stat", {'Stat': stat, 'Group': kwargs['Group']})})
    options.append({"key": ("<", "back"), "desc": "Go back to Group Selection", "goto": "menu_select_group"})
    if not pointsleft:
        options.append({"key": (">", "accept", "continue"), "desc": "Accept these stats.", "goto": "menu_accept_stats"})
    return text, options


def menu_select_merit(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    if 'Merits' in mt.temp_data.keys():
        mt.option_list['Merits']['Points'] = mt.option_list['Merits']['MaxPoints'] - helper.get_cg_points_spent(mt.temp_data['Merits'])
    points = mt.option_list['Merits']['Points']
    pointsleft = get_remaining_points(mt.option_list)
    text = str(helper.get_cg_data(mt.template, mt.headers, mt.temp_data, highlight_column=kwargs['Group'], for_purchase=True, datatype='merits', caller=caller, points_left=pointsleft))
    text += '\n|y%d|n points left to spend in this group.' % points
    options = []
    for stat in sorted(mt.race_template[kwargs['Group']]):
        options.append({"desc": stat, "goto": ("menu_adjust_merit", {'Stat': stat, 'Group': kwargs['Group']})})
    options.append({"key": ("<", "back"), "desc": "Go back to Group Selection", "goto": "menu_set_merits"})
    if not pointsleft:
        options.append({"key": (">", "accept", "continue"), "desc": "Accept these stats.", "goto": "menu_accept_stats"})
    return text, options


def menu_adjust_stat(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    text = str(helper.get_cg_data(mt.template, mt.headers, mt.temp_data, highlight_stat=kwargs['Stat'], for_purchase=True, caller=caller))
    options = []
    pointsleft = get_remaining_points(mt.option_list)
    stat = kwargs['Stat']
    group = kwargs['Group']
    points = mt.option_list[group]['Points']
    text += '\n|y%d|n points left to spend in this group.' % points
    maxpoints = mt.option_list[group]['MaxPoints']
    if (points > 0 and mt.temp_data[group][stat] < 4) or (points > 1 and mt.temp_data[group][stat] < 5):
        cost = 1
        if mt.temp_data[group][stat] >= 4:
            cost = 2
        desc = 'Increment %s by |yone|n point (Cost: |y%d|n)' % (kwargs['Stat'], cost)
        options.append({"key": ("+", "add", "increment"), "desc": desc, "goto": (_adjust_stat, {'Stat': stat, 'Amount': 1, 'Cost': cost, 'Group': group})})
    if (points <= maxpoints and mt.temp_data[group][stat] > mt.base_stat):
        cost = -1
        if mt.temp_data[group][stat] >= 5:
            cost = -2
        desc = 'Decrement %s by |yone|n point (Refund |y%d|n)' % (kwargs['Stat'], cost)
        options.append({"key": ("-", "subtract", "sub", "dec", "decrement"), "desc": desc, "goto": (_adjust_stat, {'Stat': stat, 'Amount': -1, 'Cost': cost, 'Group': group})})
    options.append({"key": ("<", "back"), "desc": "Go back to Stat Selection", "goto": ("menu_select_stat", {'Stat': stat, 'Group': group})})
    if not pointsleft:
        options.append({"key": (">", "accept", "continue"), "desc": "Accept these stats.", "goto": "menu_accept_stats"})
    return text, options


def menu_adjust_merit(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    text = ''
    # text = str(helper.get_cg_data(mt.template, mt.headers, mt.temp_data, datatype='merits', highlight_stat=kwargs['Stat'], for_purchase=True, caller=caller))
    options = []
    pointsleft = get_remaining_points(mt.option_list)
    stat = kwargs['Stat']
    merit = helper.parse_merit(mt.race_template[kwargs['Group']][kwargs['Stat']])
    points = mt.option_list['Merits']['Points']
    text += '\nEffect: %s' % merit['Effect']
    if merit['Prereqs']:
        text += '\nPrerequisites:\n%s' % helper.merit_check_prereqs(caller, merit)
    text += '\n|y%d|n points left to spend in this group.' % points
    maxpoints = mt.option_list['Merits']['MaxPoints']
    if helper.merit_can_buy(caller, merit, pointsleft):
        if not stat in list(mt.temp_data[kwargs['Group']].keys()) or merit['Multibuy']:

            if len(merit['Cost']) == 1:
                level = merit['Cost'][0]
                cost = level
                if cost > 4:
                    cost = cost + (cost - 4)
                if merit['Multibuy']:
                    options.append({"key": ("+"), "desc": "Purchase this merit", "goto": (
                    "menu_merit_subcategory", {'Stat': stat, 'Group': kwargs['Group'], 'Category': None, 'Cost': cost, 'Level': level})})
                else:
                    options.append({"key": ("+"), "desc": "Purchase this merit",
                                "goto": (_buy_merit, {'Stat': stat, 'Group': kwargs['Group'], 'Level': level, 'Cost': cost})})
            else:
                for level in merit['Cost']:
                    cost = level
                    if cost > 4:
                        cost = cost + (cost - 4)
                    if cost <= mt.option_list['Merits']['Points']:
                        if merit['Multibuy']:
                            options.append({"key": ('%s' % level), "desc": "Purchase this merit at %s dots." % level, "goto": ("menu_merit_subcategory", {'Level': level, 'Stat': stat, 'Group': kwargs['Group'], 'Category': None, 'Cost': cost})})
                        else:
                            options.append({"key": ('%s' % level), "desc": "Purchase this merit at %s dots" % level, "goto": (_buy_merit, {'Level': level, 'Stat': stat, 'Group': kwargs['Group'], 'Cost': cost})})
    if stat in list(mt.temp_data[kwargs['Group']].keys()):
        playerstat = mt.temp_data[kwargs['Group']][stat]
        if str(playerstat).isdigit():
            cost = playerstat
            if cost > 4:
                cost = cost + (cost - 4)
            options.append({"key": ("-"), "desc": "Sell this merit back for %s points" % cost, "goto": (_sell_merit, {'Level': playerstat, 'Stat': stat, 'Group': kwargs['Group'], 'Cost': cost})})
        else:
            for substat in playerstat.keys():
                level = playerstat[substat]
                cost = level
                if cost > 4:
                    cost = cost + (cost - 4)
                options.append({"key": ("%s" % substat), "desc": "Sell this merit back for %s points" % cost, "goto": (_sell_merit, {'Level': level, 'CustomCat': substat, 'Stat': stat, 'Group': kwargs['Group'], 'Cost': cost})})
    options.append({"key": ("<", "back", "exit"), "desc": "Go back to Stat Selection", "goto": ("menu_select_merit", {'Stat': stat, 'Group': kwargs['Group']})})
    if not pointsleft:
        options.append({"key": (">", "accept", "continue"), "desc": "Accept these stats.", "goto": "menu_accept_stats"})
    return text, options


def menu_merit_subcategory(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    text = ''
    merit = helper.parse_merit(mt.race_template[kwargs['Group']][kwargs['Stat']])
    prev_entry = kwargs.get("prev_entry") if "prev_entry" in kwargs.keys() else None
    if prev_entry:
        text = "Current category: %s\nEnter category for %s" % (prev_entry, kwargs['Stat'])
    else:
        text = "Enter category for %s" % kwargs['Stat']
    options = [{"key": "_default", "goto": (_set_merit_category,{"Stat": kwargs['Stat'], "Group": kwargs['Group'], "Cost": kwargs['Cost'], "Level": kwargs['Level'], "prev_entry": prev_entry})}]
    return text, options

def _set_merit_category(caller, raw_string, **kwargs):
    inp = raw_string.strip()

    prev_entry = kwargs.get("prev_entry")

    if not inp:
        # a blank input either means OK or Abort
        if prev_entry:
            caller.msg("{} accepted.".format(prev_entry))
            node, args = _buy_merit(caller=caller, raw_string=raw_string, Stat=kwargs['Stat'], CustomCat=prev_entry, Group=kwargs['Group'], Cost=kwargs['Cost'], Level=kwargs['Level'])
            return node, args
        else:
            caller.msg("Aborted.")
        return "menu_adjust_merit", {'Stat': kwargs['Stat'], 'Group': kwargs['Group']}
    else:
        # re-run old node, but pass in the name givens
        return None, {"prev_entry": inp, 'Stat': kwargs['Stat'], 'Group': kwargs['Group'], 'Cost': kwargs['Cost'], 'Level': kwargs['Level']}


def _buy_merit(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    customcat = kwargs['CustomCat'] if 'CustomCat' in kwargs.keys() else None
    oldstatcost = 0
    if customcat:
        if kwargs['Stat'] in mt.temp_data[kwargs['Group']].keys():
            if customcat in mt.temp_data[kwargs['Group']][kwargs['Stat']].keys():
                oldstatcost = mt.temp_data[kwargs['Group']][kwargs['Stat']][customcat]
            mt.temp_data[kwargs['Group']][kwargs['Stat']][customcat] = kwargs['Level']
            logger.log_file('%s purchased %s (%s) %s for %s points'% (caller.name, kwargs['Stat'], customcat, kwargs['Level'], kwargs['Cost']))
        else:
            mt.temp_data[kwargs['Group']][kwargs['Stat']] = {customcat: kwargs['Level']}
            logger.log_file('%s purchased %s %s for %s points'% (caller.name, kwargs['Stat'], kwargs['Level'], kwargs['Cost']))
    else:
        mt.temp_data[kwargs['Group']][kwargs['Stat']] = kwargs['Level']
    mt.option_list['Merits']['Points'] -= (kwargs['Cost'] - oldstatcost)
    return "menu_select_merit", {'Group': kwargs['Group']}

def _sell_merit(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    customcat = kwargs['CustomCat'] if 'CustomCat' in kwargs.keys() else None
    if customcat:
        if customcat in mt.temp_data[kwargs['Group']][kwargs['Stat']].keys():
            del mt.temp_data[kwargs['Group']][kwargs['Stat']][customcat]
            if len(mt.temp_data[kwargs['Group']][kwargs['Stat']]) == 0:
                del mt.temp_data[kwargs['Group']][kwargs['Stat']]
            logger.log_file('%s sold %s (%s) %s for %s points'% (caller.name, kwargs['Stat'], customcat, kwargs['Level'], kwargs['Cost']))

    else:
        del mt.temp_data[kwargs['Group']][kwargs['Stat']]
        logger.log_file('%s sold %s %s for %s points' % (caller.name, kwargs['Stat'], kwargs['Level'], kwargs['Cost']))

    mt.option_list['Merits']['Points'] += kwargs['Cost']
    return "menu_select_merit", {'Group': kwargs['Group']}


def menu_merit_select_cost(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    merit = helper.parse_merit(mt.race_template[kwargs['Group']][kwargs['Stat']])

def _adjust_stat(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    mt.temp_data[kwargs['Group']][kwargs['Stat']] += kwargs['Amount']
    mt.option_list[kwargs['Group']]['Points'] -= kwargs['Cost']
    pluralcost = ''
    pluralamount = ''
    if abs(kwargs['Amount']) > 1:
        pluralamount = 's'
    if abs(kwargs['Cost']) > 1:
        pluralcost = 's'
    logger.log_file(
        '%s adjusted %s by %s dot%s for %s point%s' % (caller.name, kwargs['Stat'], kwargs['Amount'], pluralamount, kwargs['Cost'], pluralcost))

    return None, {'Stat': kwargs['Stat'], 'Group': kwargs['Group']}

def menu_confirm_accept(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    option_list = mt.option_list
    pointsleft = get_remaining_points(mt.option_list)
    text = str(helper.get_cg_data(mt.template, mt.headers, mt.temp_data, for_purchase=True, caller=caller))
    text += "\n\nAre you sure?  You still have |y%d|n points remaining to spend." % pointsleft
    options = []
    options.append({"key": ("yes", "y"), "goto": "menu_accept_stats"})
    options.append({"key": ("no", "n", "back", "quit", "exit"), "goto": "menu_select_group"})
    return text, options


def menu_accept_stats(caller, raw_string, **kwargs):
    mt = caller.ndb._menutree
    for item in list(mt.temp_data.keys()):
        if not mt.temp_data[item]:
            del mt.temp_data[item]
        caller.attributes.add(mt.current_data, mt.temp_data)
        segment = mt.current_data.split('_')[1].capitalize()
        caller.chargenfinished(segment=segment, value=True)
    if not caller.chargenfinished():
        evmenu.EvMenu(caller, "wodsystem.menu", startnode="menu_chargen", cmd_on_exit=None)
    else:
        pass