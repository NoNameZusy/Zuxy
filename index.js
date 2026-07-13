const { Client, GatewayIntentBits, PermissionsBitField, EmbedBuilder } = require("discord.js");
const fs = require("fs");

const client = new Client({
 intents: [
   GatewayIntentBits.Guilds,
   GatewayIntentBits.GuildMessages,
   GatewayIntentBits.MessageContent,
   GatewayIntentBits.GuildMembers
 ]
});

client.login(process.env.TOKEN);

const SETTINGS_FILE = "./settings.json";

function loadSettings() {
 try {
   return JSON.parse(fs.readFileSync(SETTINGS_FILE, "utf8"));
 } catch {
   return {};
 }
}

function saveSettings(data) {
 fs.writeFileSync(SETTINGS_FILE, JSON.stringify(data, null, 2));
}

let settings = loadSettings();

function getGuild(guildId) {
 if (!settings[guildId]) settings[guildId] = { welcome: null, autoroles: [], automsg: [] };
 if (!settings[guildId].automsg) settings[guildId].automsg = [];
 if (!settings[guildId].autoroles) settings[guildId].autoroles = [];
 return settings[guildId];
}

client.on("ready", () => {
 console.log(`Zuxy is online as ${client.user.tag}`);
});

client.on("guildMemberAdd", async (member) => {
 const guildSettings = getGuild(member.guild.id);

 for (const roleId of guildSettings.autoroles) {
   const role = member.guild.roles.cache.get(roleId);
   if (role) await member.roles.add(role).catch(console.error);
 }

 if (!guildSettings.welcome) return;
 const channel = member.guild.channels.cache.get(guildSettings.welcome.channelId);
 if (!channel) return;
 const finalMessage = guildSettings.welcome.message.replace("{user}", `<@${member.id}>`);
 channel.send(finalMessage);
});

client.on("messageCreate", async (message) => {
 if (message.author.bot) return;

 const args = message.content.split(" ");
 const command = args[0].toLowerCase();
 const member = message.mentions.members.first();

 // 🤖 Auto message reply
 if (!message.content.startsWith("!")) {
   const guildSettings = getGuild(message.guild.id);
   const msgLower = message.content.toLowerCase().trim();
   for (const entry of guildSettings.automsg) {
     if (msgLower.includes(entry.trigger.toLowerCase())) {
       return message.reply(entry.response);
     }
   }
 }

 // ❓ HELP
 if (command === "!help") {
   const embed = new EmbedBuilder()
     .setTitle("📋 Zuxy — Command List")
     .setColor(0x5865f2)
     .setDescription("Here are all available commands:")
     .addFields(
       { name: "!role @role @user", value: "Gives the mentioned role to the mentioned user.\n**Example:** `!role @Mod @John`", inline: false },
       { name: "!unrole @role @user", value: "Removes the mentioned role from the mentioned user.\n**Example:** `!unrole @Mod @John`", inline: false },
       { name: "!kick @user [reason]", value: "Kicks the mentioned user from the server.", inline: false },
       { name: "!ban @user [reason]", value: "Bans the mentioned user from the server.", inline: false },
       { name: "!clear <amount>", value: "Deletes the specified number of messages (1-100).", inline: false },
       {
         name: "!welcome #channel <message>",
         value: "Sets the welcome message.\n• `{user}` = new member mention\n**Example:** `!welcome #welcome Hello {user}!`",
         inline: false
       },
       { name: "!welcome off", value: "Disables the welcome message.", inline: false },
       { name: "!autorole @role", value: "Adds a role to the auto role list. Run multiple times to add multiple roles.", inline: false },
       { name: "!unauto @role", value: "Removes a specific role from the auto role list.", inline: false },
       { name: "!autorole off", value: "Clears all roles from the auto role list.", inline: false },
       {
         name: "!automsg <trigger> | <response>",
         value: "Sets an auto reply. Case-insensitive.\n**Example:** `!automsg hi | Hello there!`",
         inline: false
       },
       { name: "!delauto <trigger>", value: "Removes an auto reply by its trigger.\n**Example:** `!delauto hi`", inline: false },
       { name: "!listauto", value: "Lists all current auto reply triggers and responses.", inline: false },
       {
         name: "!show <type>",
         value: "Shows current settings.\n• `!show welcome` — welcome message & channel\n• `!show autorole` — auto role list\n• `!show automsg` — all auto replies\n• `!show all` — everything at once",
         inline: false
       },
       { name: "!help", value: "Shows this command list.", inline: false }
     )
     .setFooter({ text: "Zuxy • [] = optional, <> = required • Settings persist after restarts" })
     .setTimestamp();

   return message.reply({ embeds: [embed] });
 }

 // ❌ No mention check
 if (!member && ["!kick", "!ban"].includes(command)) {
   return message.reply("❌ Please mention a user. Example: !kick @user");
 }

 // 🎖️ ROLE
 if (command === "!role") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageRoles))
     return message.reply("❌ You need the **Manage Roles** permission to use this command.");
   const role = message.mentions.roles.first();
   const target = message.mentions.members.first();
   if (!role || !target)
     return message.reply("❌ Please mention a role and a user. Example: `!role @Mod @John`");
   try {
     await target.roles.add(role);
     return message.reply(`✅ **${role.name}** has been given to **${target.user.tag}**.`);
   } catch (err) {
     console.log(err);
     return message.reply("❌ Error: Permission or role hierarchy issue.");
   }
 }

 // 🚫 UNROLE
 if (command === "!unrole") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageRoles))
     return message.reply("❌ You need the **Manage Roles** permission to use this command.");
   const role = message.mentions.roles.first();
   const target = message.mentions.members.first();
   if (!role || !target)
     return message.reply("❌ Please mention a role and a user. Example: `!unrole @Mod @John`");
   try {
     await target.roles.remove(role);
     return message.reply(`✅ **${role.name}** has been removed from **${target.user.tag}**.`);
   } catch (err) {
     console.log(err);
     return message.reply("❌ Error: Permission or role hierarchy issue.");
   }
 }

 // 👢 KICK
 if (command === "!kick") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.KickMembers))
     return message.reply("❌ You need the **Kick Members** permission to use this command.");
   const reason = args.slice(2).join(" ") || "No reason provided";
   try {
     await member.kick(reason);
     return message.reply(`✅ **${member.user.tag}** has been kicked. Reason: ${reason}`);
   } catch (err) {
     console.log(err);
     return message.reply("❌ Error: Could not kick the user. Check role hierarchy and permissions.");
   }
 }

 // 🔨 BAN
 if (command === "!ban") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.BanMembers))
     return message.reply("❌ You need the **Ban Members** permission to use this command.");
   const reason = args.slice(2).join(" ") || "No reason provided";
   try {
     await member.ban({ reason });
     return message.reply(`✅ **${member.user.tag}** has been banned. Reason: ${reason}`);
   } catch (err) {
     console.log(err);
     return message.reply("❌ Error: Could not ban the user. Check role hierarchy and permissions.");
   }
 }

 // 🗑️ CLEAR
 if (command === "!clear") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageMessages))
     return message.reply("❌ You need the **Manage Messages** permission to use this command.");
   const amount = parseInt(args[1]);
   if (!amount || isNaN(amount) || amount < 1 || amount > 100)
     return message.reply("❌ Please enter a valid number. Example: !clear 10 (between 1-100)");
   try {
     const deleted = await message.channel.bulkDelete(amount + 1, true);
     const confirmMsg = await message.channel.send(`✅ Successfully deleted **${deleted.size - 1}** messages.`);
     setTimeout(() => confirmMsg.delete().catch(() => {}), 3000);
   } catch (err) {
     console.log(err);
     return message.reply("❌ Error: Could not delete messages. (Messages older than 14 days cannot be deleted)");
   }
 }

 // 🎉 WELCOME
 if (command === "!welcome") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageGuild))
     return message.reply("❌ You need the **Manage Server** permission to use this command.");

   const fullContent = message.content.slice("!welcome ".length).trim();

   if (fullContent.toLowerCase() === "off") {
     getGuild(message.guild.id).welcome = null;
     saveSettings(settings);
     return message.reply("✅ Welcome message has been disabled.");
   }

   const targetChannel = message.mentions.channels.first();
   if (!targetChannel)
     return message.reply("❌ Please mention a channel. Example: `!welcome #welcome Hello {user}!`");

   const welcomeMessage = fullContent.replace(/<#\d+>/, "").trim();
   if (!welcomeMessage)
     return message.reply("❌ Please provide a welcome message after the channel.");

   getGuild(message.guild.id).welcome = { channelId: targetChannel.id, message: welcomeMessage };
   saveSettings(settings);

   return message.reply(
     `✅ Welcome message set!\n📢 **Channel:** <#${targetChannel.id}>\n💬 **Message preview:** ${welcomeMessage.replace("{user}", "@newmember")}`
   );
 }

 // 🤖 AUTOROLE
 if (command === "!autorole") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageRoles))
     return message.reply("❌ You need the **Manage Roles** permission to use this command.");

   const fullContent = message.content.slice("!autorole ".length).trim();

   if (fullContent.toLowerCase() === "off") {
     getGuild(message.guild.id).autoroles = [];
     saveSettings(settings);
     return message.reply("✅ All auto roles have been cleared.");
   }

   const role = message.mentions.roles.first();
   if (!role)
     return message.reply("❌ Please mention a role. Example: `!autorole @Member`");

   const guildSettings = getGuild(message.guild.id);
   if (!guildSettings.autoroles.includes(role.id)) {
     guildSettings.autoroles.push(role.id);
     saveSettings(settings);
   }

   const allRoles = guildSettings.autoroles.map(id => `<@&${id}>`).join(", ");
   return message.reply(`✅ **${role.name}** added to auto role list.\n📋 **Current auto roles:** ${allRoles}`);
 }

 // 🚫 UNAUTO
 if (command === "!unauto") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageRoles))
     return message.reply("❌ You need the **Manage Roles** permission to use this command.");

   const role = message.mentions.roles.first();
   if (!role)
     return message.reply("❌ Please mention a role. Example: `!unauto @Member`");

   const guildSettings = getGuild(message.guild.id);
   if (!guildSettings.autoroles.includes(role.id))
     return message.reply(`❌ **${role.name}** is not in the auto role list.`);

   guildSettings.autoroles = guildSettings.autoroles.filter(id => id !== role.id);
   saveSettings(settings);

   const remaining = guildSettings.autoroles.map(id => `<@&${id}>`).join(", ") || "None";
   return message.reply(`✅ **${role.name}** removed from auto role list.\n📋 **Remaining auto roles:** ${remaining}`);
 }

 // 💬 AUTOMSG
 if (command === "!automsg") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageMessages))
     return message.reply("❌ You need the **Manage Messages** permission to use this command.");

   const fullContent = message.content.slice("!automsg ".length).trim();
   const separatorIndex = fullContent.indexOf("|");

   if (separatorIndex === -1)
     return message.reply("❌ Please use `|` to separate trigger and response.\n**Example:** `!automsg hi | Hello there!`");

   const trigger = fullContent.slice(0, separatorIndex).trim();
   const response = fullContent.slice(separatorIndex + 1).trim();

   if (!trigger || !response)
     return message.reply("❌ Trigger or response cannot be empty.\n**Example:** `!automsg hi | Hello there!`");

   const guildSettings = getGuild(message.guild.id);
   const existing = guildSettings.automsg.findIndex(e => e.trigger.toLowerCase() === trigger.toLowerCase());

   if (existing !== -1) {
     guildSettings.automsg[existing].response = response;
     saveSettings(settings);
     return message.reply(`✅ Auto reply for **"${trigger}"** has been updated.`);
   }

   guildSettings.automsg.push({ trigger, response });
   saveSettings(settings);
   return message.reply(`✅ Auto reply set!\n🔤 **Trigger:** ${trigger}\n💬 **Response:** ${response}`);
 }

 // ❌ DELAUTO
 if (command === "!delauto") {
   if (!message.member.permissions.has(PermissionsBitField.Flags.ManageMessages))
     return message.reply("❌ You need the **Manage Messages** permission to use this command.");

   const trigger = message.content.slice("!delauto ".length).trim();
   if (!trigger)
     return message.reply("❌ Please provide a trigger to delete. Example: `!delauto hi`");

   const guildSettings = getGuild(message.guild.id);
   const index = guildSettings.automsg.findIndex(e => e.trigger.toLowerCase() === trigger.toLowerCase());

   if (index === -1)
     return message.reply(`❌ No auto reply found for **"${trigger}"**.`);

   guildSettings.automsg.splice(index, 1);
   saveSettings(settings);
   return message.reply(`✅ Auto reply for **"${trigger}"** has been removed.`);
 }

 // 📋 LISTAUTO
 if (command === "!listauto") {
   const guildSettings = getGuild(message.guild.id);

   if (guildSettings.automsg.length === 0)
     return message.reply("❌ No auto replies set yet. Use `!automsg trigger | response` to add one.");

   const embed = new EmbedBuilder()
     .setTitle("💬 Auto Reply List")
     .setColor(0x5865f2)
     .setDescription(
       guildSettings.automsg.map((e, i) =>
         `**${i + 1}.** Trigger: \`${e.trigger}\`\n↩️ Response: ${e.response}`
       ).join("\n\n")
     )
     .setFooter({ text: `${guildSettings.automsg.length} auto reply(s) active` })
     .setTimestamp();

   return message.reply({ embeds: [embed] });
 }

 // 👁️ SHOW
 if (command === "!show") {
   const guildSettings = getGuild(message.guild.id);
   const sub = args[1]?.toLowerCase();

   if (!sub)
     return message.reply("❌ Please specify what to show.\n• `!show welcome`\n• `!show autorole`\n• `!show automsg`\n• `!show all`");

   const embeds = [];

   if (sub === "welcome" || sub === "all") {
     const embed = new EmbedBuilder()
       .setTitle("👋 Welcome Settings")
       .setColor(0x5865f2);

     if (!guildSettings.welcome) {
       embed.setDescription("❌ No welcome message set.");
     } else {
       embed.addFields(
         { name: "📢 Channel", value: `<#${guildSettings.welcome.channelId}>`, inline: true },
         { name: "💬 Message", value: guildSettings.welcome.message.replace("{user}", "@newmember"), inline: false }
       );
     }
     embeds.push(embed);
   }

   if (sub === "autorole" || sub === "all") {
     const embed = new EmbedBuilder()
       .setTitle("🤖 Auto Role Settings")
       .setColor(0x5865f2);

     if (!guildSettings.autoroles || guildSettings.autoroles.length === 0) {
       embed.setDescription("❌ No auto roles set.");
     } else {
       embed.setDescription(guildSettings.autoroles.map((id, i) => `**${i + 1}.** <@&${id}>`).join("\n"));
     }
     embeds.push(embed);
   }

   if (sub === "automsg" || sub === "all") {
     const embed = new EmbedBuilder()
       .setTitle("💬 Auto Reply Settings")
       .setColor(0x5865f2);

     if (!guildSettings.automsg || guildSettings.automsg.length === 0) {
       embed.setDescription("❌ No auto replies set.");
     } else {
       embed.setDescription(
         guildSettings.automsg.map((e, i) =>
           `**${i + 1}.** Trigger: \`${e.trigger}\`\n↩️ Response: ${e.response}`
         ).join("\n\n")
       );
     }
     embeds.push(embed);
   }

   if (embeds.length === 0)
     return message.reply("❌ Unknown option. Use `welcome`, `autorole`, `automsg`, or `all`.");

   return message.reply({ embeds });
 }
});
