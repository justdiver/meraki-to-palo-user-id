# Background

This will detail the process of exporting all users for an organization in Meraki using their API, parsing this into a usable XML format, and then importing that into the Palo Alto firewall using their API.  

## Required Understanding

You should have an understanding of the Meraki dashboard, the Palo Alto ui, how APIs work, and at least basic knowledge of python. 

## Why even do this? 

Palo Alto has the ability to map an IP address to a username. You can then apply policies based off of that username.  This also makes it much easier to look at the monitor log and know who is doing what on your network, without needing to take extra steps to figure out who an IP actually is.  

"But doesn't Palo Alto have an agent to do this?"  Yes. In most cases.  They have a wealth of documentation which you can find here: https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-admin/user-id/user-id-overview  The difficulty is that in my environment, 95% of my users are not authenticating against our Active Directory servers directly.  We have an 802.1x wireless network that our users connect to. "But doesn't Palo Alto have a way to pull that information?"  Again, yes.  In most cases.  In my environment, when a user connects to the network, Microsoft NPS Radius does not log the ip address of the client that is connecting.  Instead the wireless access point is seen as the client.  This does me no good. Meraki on the otherhand does record this information.  So the challenge is to get this info out of Meraki, and into Palo Alto. 

## Step 1.

First thing to do is get your Meraki API key. Information on this process can be found here: https://documentation.meraki.com/General_Administration/Other_Topics/Cisco_Meraki_Dashboard_API

After you have your API key, next head over to the Meraki automation github page: https://github.com/meraki/automation-scripts You're going to want to grab the orgclientscsv.py script.  For my purpose, I don't need everything that this script pulls.  Under the line "for client in networkClients:" comment out everything except for client ip and client user. And then do the same under "csvHeader = ','.join(\[" This will limit how much information we actually have to parse through.  Next find the line that say "for net in networks:" and on the next line, add the following to the query: 'perPage':250,'timespan':86400.  This will limit the time we're searching to 24 hours and return 250 clients per page.  This makes the script run MUCH faster.  You can modify these to suit your needs, but this was fine for me. 

Once you run this script, you'll have a file that contains all of the users on your meraki dashboard and the last IP address that they used (in the last 24 hours obviously).  The file should contain something like this: 
```
clientIpv4Address,user
10.10.10.10,fooser0
10.10.10.11,fooser1
```

## Step 2.

Next we need to parse this file into something that the Palo Alto API will accept.  Based on their documentation found here: https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-panorama-api/pan-os-xml-api-request-types/apply-user-id-mapping-and-populate-dynamic-address-groups-api We can see that we need our XML file to be formatted as such:
```<uid-message> 
     <version>1.0</version> 
     <type>update</type> 
     <payload> 
          <login> 
               <entry name="domain\uid1" ip="10.1.1.1" timeout="20"> 
               </entry> 
          </login> 
          <groups> 
               <entry name="group1"> 
                    <members> 
                         <entry name="user1"/> 
                         <entry name="user2"/> 
                    </members> 
               </entry> 
               <entry name="group2"> 
                    <members> 
                         <entry name="user3"/> 
                    </members> 
               </entry> 
          </groups> 
     </payload> 
</uid-message>
```
I'm not doing any group modification, so we can trim this down to:
```
<uid-message> 
     <version>1.0</version> 
     <type>update</type> 
     <payload> 
          <login> 
               <entry name="domain\fooser2" ip="10.10.10.10" timeout="300" \> 
               <entry name="domain\fooser1" ip="10.10.10.11" timeout="300" \>
          </login> 
     </payload> 
</uid-message>
```
Take note of the self closing tag and the timeout which I have set to 300.  To get our CSV from Meraki into this XML format, we can run a python script. Credit to Tyler Covault for writing this for me.  I tried my hand at the python, but I am woefully inexperienced at it. It's included in this repo as XML_Builder.py

After running the XML_Builder, it will spit out a nicely formatted XML file that contains a single line for each user.  *A couple notes on this: 1). Users can show up twice. As they should. But if you have shared users, an account for iPads to connect with for example, than you may want to exclude that user from the output. 2). We ended up excluding APIPA addresses as a couple of those somehow ended up in the export from Meraki. 3). We have this script removing the CSV after it runs, to prevent file collisions.*

## Step 3

Next, you need a Palo Alto API key, and we need to push the XML file to the firewall. You can find info on getting your Palo Alto API key here: https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-panorama-api/get-started-with-the-pan-os-xml-api/get-your-api-key  Doublecheck your API key lifetime. https://docs.paloaltonetworks.com/pan-os/10-1/pan-os-admin/firewall-administration/manage-firewall-administrators/configure-administrative-accounts-and-authentication/configure-api-key-lifetime  I do not recommend an infinite lifetime, but you can set it to whatever you want. 

API key in hand, we can plug this into another Python script to do the actual push.  pa-post-api.py in this repo. If you've done everything correct, you can hop over to the Monitor tab on your firewall and check the user-id mappings. You can filter this with `( datasourcename eq XMLAPI )` to show just the user-ids that came from the API (in case you have other sources as well). 
