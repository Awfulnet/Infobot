Infobot
=======

Infobot stores info about users on [Awfulnet](http://awfulnet.org/). This open-source version is based on [James](https://github.com/svkampen/James) and is designed to replace old infobot. 
While being backward compatible it has many new features and upgrades including, but not limited to:

* **Unicode support** - Allows to use all thinkable characters, such as emoji or chinese, in users' infos.
* **No length limit** - Infobot's database sets no limit on the length of infos. The only limitation is IRC's message length.
* **Info history** - All individual info edits are kept, which opens up new possibilities like restoring old info. *(not used yet)*
* **Easier info editing** - Let users easily do replacements in their info without needing to add their entire info again using powerful `sed` syntax.
* **Multi-level aliases** - Overcomes old infobot's limitation and makes it possible to have situations like this:
  <br>
  A sets alias to B and B sets alias to C. Now when checking A's info it returns C's info.
* **Public access** - As Infobot stores its data in a PostgreSql database we can allow other bots directly have read-only access to user info
* **Open-sourced-ness** - Due to being a central bot on the network it must be kept up to date and liked by its users. 
This allows everyone to to point out any bugs or submit changes, continuously making Infobot better.
