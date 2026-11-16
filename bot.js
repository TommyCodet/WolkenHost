const mineflayer=require('mineflayer'),fs=require('fs');
const configPath=process.argv[2];let cfg;
if(configPath)cfg=JSON.parse(fs.readFileSync(configPath,'utf8'));
else{for(const key of ['SERVER_HOST'])if(!process.env[key])throw new Error('Missing '+key);
cfg={serverHost:process.env.SERVER_HOST,serverPort:Number(process.env.SERVER_PORT||25565),mcVersion:process.env.MC_VERSION||'auto',afkEnabled:/^(1|true|yes|on)$/i.test(process.env.AFK_ENABLED||'true'),afkCommand:process.env.AFK_COMMAND||'/afk on',autoReconnect:/^(1|true|yes|on)$/i.test(process.env.AUTO_RECONNECT||'true'),reconnectDelay:Number(process.env.RECONNECT_DELAY||10)};}
const host=String(cfg.serverHost||''),port=Number(cfg.serverPort||25565),version=cfg.mcVersion==='auto'||!cfg.mcVersion?false:cfg.mcVersion;
const delay=Math.min(300,Math.max(5,Number(cfg.reconnectDelay||10)))*1000;
if(!host||!Number.isInteger(port)||port<1||port>65535)throw new Error('Invalid Minecraft server host/port');
if(!['auto','1.21.1','1.20.4','1.19.4',false].includes(cfg.mcVersion||'auto'))throw new Error('Unsupported Minecraft version');
let bot,stopping=false,timer,afkTimer;
function connect(){if(stopping)return;console.log('Connecting to Minecraft server...');bot=mineflayer.createBot({host,port,username:'WolkeHost',auth:'microsoft',version});
bot.once('login',()=>{console.log('Minecraft login event received');if(cfg.afkEnabled&&cfg.afkCommand)afkTimer=setTimeout(()=>{if(bot&&bot.player)bot.chat(String(cfg.afkCommand).slice(0,100))},2500)});
bot.on('kicked',reason=>console.log('Disconnected by server:',String(reason).slice(0,300)));bot.on('error',error=>console.error('Minecraft connection error:',error.message));
bot.once('end',()=>{clearTimeout(afkTimer);console.log('Connection ended');if(!stopping&&cfg.autoReconnect)timer=setTimeout(connect,delay)});}
function shutdown(){if(stopping)return;stopping=true;clearTimeout(timer);clearTimeout(afkTimer);if(bot){try{bot.quit('WolkeHost stopping')}catch(_){}}setTimeout(()=>process.exit(0),700).unref();}
process.on('SIGTERM',shutdown);process.on('SIGINT',shutdown);connect();
