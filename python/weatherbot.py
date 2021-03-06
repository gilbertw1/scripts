#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# Copyright (c) 2014-2015 by deflax <daniel@deflax.net>
#
#       Weechat WeatherBot using WUnderground API
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

SCRIPT_NAME = "weatherbot"
VERSION = "0.4"

helptext = """
Get your own API key from http://www.wunderground.com/weather/api/
and act as a weatherbot :)

Hugs to all friends from #clanchill @ quakenet \o/
"""

import weechat, ast

script_options = {
    "enabled" : "off",
    "units" : "metric",
    "trigger" : "!weather",
    "apikey" : "0000000000000" }

def weebuffer(reaction_buf):
    rtnbuf = kserver + "," + kchannel
    buffer = weechat.info_get("irc_buffer", rtnbuf)
    weechat.command(buffer, "/msg " + kchannel + " " + reaction_buf)

def wu_autoc(data, command, return_code, out, err):
    global jname
    if return_code == weechat.WEECHAT_HOOK_PROCESS_ERROR:
        weechat.prnt("", "Error with command '%s'" % command)
        return weechat.WEECHAT_RC_OK
    if return_code > 0:
        weechat.prnt("", "return_code = %d" % return_code)
    if err != "":
        weechat.prnt("", "stderr: %s" % err)
    if out != "":
        i = ast.literal_eval(out)
        loc_id = ""
        try:
            loc_id = i['RESULTS'][0]['l']
        except:
            reaction = 'Invalid query. Try again.'
            weebuffer(reaction)
            return weechat.WEECHAT_RC_OK
        jname = i['RESULTS'][0]['name']
        if jname == "":
            reaction = 'Unable to locate query.'
            weebuffer(reaction)
            return weechat.WEECHAT_RC_OK
        else:
            pass
        cond_url = 'url:http://api.wunderground.com/api/' + apikey + '/conditions' + loc_id + '.json'
        cond_hook = weechat.hook_process(cond_url, 30 * 1000, "wu_cond", "")
    return weechat.WEECHAT_RC_OK

def wu_cond(data, command, return_code, out, err):
    if return_code == weechat.WEECHAT_HOOK_PROCESS_ERROR:
        weechat.prnt("", "Error with command '%s'" % command)
        return weechat.WEECHAT_RC_OK
    if return_code > 0:
        weechat.prnt("", "return_code = %d" % return_code)
    if err != "":
        weechat.prnt("", "stderr: %s" % err)
    if out != "":
        j = ast.literal_eval(out)
        try:
            jcheck = j['response']['error']['type']
            if j['response']['error']['type'] == "invalidquery":
                reaction = "Error. Try again."
                weebuffer(reaction)
                return weechat.WEECHAT_RC_OK
            if j['response']['error']['type'] == "keynotfound":
                weechat.prnt("", "Invalid API key.")
                return weechat.WEECHAT_RC_OK
        except KeyError:
            pass

        co = 'current_observation'
        reaction = '[' + jname + '] ' + j[co]['weather'] + '. Temp is '

        if units == "metric":
            windspeed = j[co]['wind_kph']
            temp = j[co]['temp_c']
            like = j[co]['feelslike_c']
            if str(temp) == str(like):
                reaction += str(temp) + "°C"
            else:
                reaction += str(temp) + "°C but feels like " + str(like) + "°C"
            if windspeed > 0:
                reaction += '. '
                reaction += str(j[co]['wind_dir']) + ' wind: ' + str(windspeed) + ' kph'
        else:
            windspeed = j[co]['wind_mph']
            temp = j[co]['temp_f']
            like = j[co]['feelslike_f']
            if str(temp) == str(like):
                reaction += str(temp) + "°F"
            else:
                reaction += str(temp) + "°F but feels like " + str(like) + "°F"
            if windspeed > 0:
                reaction += '. '
                reaction += str(j[co]['wind_dir']) + ' wind: ' + str(windspeed) + ' mph'

        humid = j[co]['relative_humidity']
        if int(humid[:-1]) > 50:
            reaction += '. Humidity: ' + j[co]['relative_humidity']
        reaction += '.'

        weebuffer(reaction)
    return weechat.WEECHAT_RC_OK

def triggerwatch(data, server, args):
    global kserver, kchannel
    if enabled == "on":
        try:
            null, srvmsg = args.split(" PRIVMSG ", 1)#
            kchannel, query = srvmsg.split(" :" + trigger + " ", 1)
        except ValueError, e:
            #weechat.prnt(e)
            return weechat.WEECHAT_RC_OK
        kserver = str(server.split(",",1)[0])
        query = query.replace(" ", "%20")
        autoc_url = 'url:http://autocomplete.wunderground.com/aq?query=' + query + '&format=JSON'
        #print(autoc_url) #debug
        autoc_hook = weechat.hook_process(autoc_url, 30 * 1000, "wu_autoc", "")
    else:
        pass
    return weechat.WEECHAT_RC_OK

weechat.register("weatherbot", "deflax", VERSION, "GPL3", "WeatherBot using the WeatherUnderground API", "", "")
weechat.hook_signal("*,irc_in_privmsg", "triggerwatch", "data")

def config_cb(data, option, value):
    """Callback called when a script option is changed."""
    global enabled, units, trigger, apikey
    if option == "plugins.var.python." + SCRIPT_NAME + ".units": units = value
    if option == "plugins.var.python." + SCRIPT_NAME + ".enabled": enabled = value
    if option == "plugins.var.python." + SCRIPT_NAME + ".trigger": trigger = value
    if option == "plugins.var.python." + SCRIPT_NAME + ".apikey": apikey = value
    return weechat.WEECHAT_RC_OK

weechat.hook_config("plugins.var.python." + SCRIPT_NAME + ".*", "config_cb", "")
for option, default_value in script_options.items():
    if not weechat.config_is_set_plugin(option):
        weechat.config_set_plugin(option, default_value)

enabled = weechat.config_string(weechat.config_get("plugins.var.python." + SCRIPT_NAME + ".enabled"))
units = weechat.config_string(weechat.config_get("plugins.var.python." + SCRIPT_NAME + ".units"))
trigger = weechat.config_string(weechat.config_get("plugins.var.python." + SCRIPT_NAME + ".trigger"))
apikey = weechat.config_string(weechat.config_get("plugins.var.python." + SCRIPT_NAME + ".apikey"))

if apikey == "0000000000000":
    weechat.prnt("", "Your API key is not set. Please sign up at www.wunderground.com/weather/api and set plugins.var.python.weatherbot.* options. Thanks.")
