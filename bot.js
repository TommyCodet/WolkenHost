const mineflayer=require('mineflayer'),fs=require('fs');
const path=process.argv[2]; if(!path) throw new Error('Usage: node bot.js data/bot-ID.json');
const cfg=JSON.parse(fs.readFileSync(path,'utf8')); let bot,stopping=false,timer;
function connect(){if(stopping)return;bot=mineflayer.createBot({host:cfg.host,port:Number(cfg.port||25565),username:'Microsoft account',auth:'microsoft',version:cfg.version||false});
 bot.once('login',()=>{console.log('Minecraft login successful');if(cfg.commandAfk)setTimeout(()=>{if(bot&&bot.player)bot.chat('/afk on')},2500)});
 bot.on('kicked',r=>console.log('Kicked:',r));bot.on('error',e=>console.error('Bot error:',e.message));
 bot.once('end',()=>{console.log('Connection ended');if(!stopping&&cfg.autoreconnect)timer=setTimeout(connect,10000)});
}
function shutdown(){stopping=true;clearTimeout(timer);if(bot){try{bot.quit('WolkeHost stopping')}catch(_){}}setTimeout(()=>process.exit(0),500)}
process.on('SIGTERM',shutdown);process.on('SIGINT',shutdown);connect();
