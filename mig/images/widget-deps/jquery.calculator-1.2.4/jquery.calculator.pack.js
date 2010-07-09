﻿/* http://keith-wood.name/calculator.html
   Calculator field entry extension for jQuery v1.2.4.
   Written by Keith Wood (kbwood{at}iinet.com.au) October 2008.
   Dual licensed under the GPL (http://dev.jquery.com/browser/trunk/jquery/GPL-LICENSE.txt) and 
   MIT (http://dev.jquery.com/browser/trunk/jquery/MIT-LICENSE.txt) licenses. 
   Please attribute the author if you use it. */
eval(function(p,a,c,k,e,r){e=function(c){return(c<a?'':e(parseInt(c/a)))+((c=c%a)>35?String.fromCharCode(c+29):c.toString(36))};if(!''.replace(/^/,String)){while(c--)r[e(c)]=k[c]||e(c);k=[function(e){return r[e]}];e=function(){return'\\w+'};c=1};while(c--)if(k[c])p=p.replace(new RegExp('\\b'+e(c)+'\\b','g'),k[c]);return p}('(w($){z p=\'v\';w 2d(){q.1o=L;q.1z=[];q.1j=11;q.2e=11;q.1k={\'6a\':[\'0\',q.V,L,\'\',\'0\',\'0\'],\'6b\':[\'1\',q.V,L,\'\',\'1\',\'1\'],\'6c\':[\'2\',q.V,L,\'\',\'2\',\'2\'],\'6d\':[\'3\',q.V,L,\'\',\'3\',\'3\'],\'6e\':[\'4\',q.V,L,\'\',\'4\',\'4\'],\'6f\':[\'5\',q.V,L,\'\',\'5\',\'5\'],\'6g\':[\'6\',q.V,L,\'\',\'6\',\'6\'],\'6h\':[\'7\',q.V,L,\'\',\'7\',\'7\'],\'6i\':[\'8\',q.V,L,\'\',\'8\',\'8\'],\'6j\':[\'9\',q.V,L,\'\',\'9\',\'9\'],\'6k\':[\'A\',q.V,L,\'1V-V\',\'A\',\'a\'],\'6l\':[\'B\',q.V,L,\'1V-V\',\'B\',\'b\'],\'6m\':[\'C\',q.V,L,\'1V-V\',\'C\',\'c\'],\'6n\':[\'D\',q.V,L,\'1V-V\',\'D\',\'d\'],\'6o\':[\'E\',q.V,L,\'1V-V\',\'E\',\'e\'],\'6p\':[\'F\',q.V,L,\'1V-V\',\'F\',\'f\'],\'14.\':[\'.\',q.V,L,\'4b\',\'6q\',\'.\'],\'14+\':[\'+\',q.1s,q.3e,\'1H 4c\',\'6r\',\'+\'],\'14-\':[\'-\',q.1s,q.3f,\'1H 4d\',\'6s\',\'-\'],\'14*\':[\'*\',q.1s,q.3g,\'1H 6t\',\'6u\',\'*\'],\'14/\':[\'/\',q.1s,q.3h,\'1H 6v\',\'6w\',\'/\'],\'14%\':[\'%\',q.W,q.4e,\'1H 6x\',\'6y\',\'%\'],\'14=\':[\'=\',q.W,q.3i,\'1H 6z\',\'6A\',\'=\'],\'+-\':[\'±\',q.W,q.4f,\'1H 6B-6C\',\'6D\',\'#\'],\'2f\':[\'4g\',q.W,q.4h,\'4g\',\'2f\',\'p\'],\'1X\':[\'1/x\',q.W,q.4i,\'1A 6E\',\'6F\',\'i\'],\'6G\':[\'2g\',q.W,q.4j,\'1A 2g\',\'6H\',\'l\'],\'4k\':[\'4l\',q.W,q.4m,\'1A 4l\',\'4k\',\'n\'],\'6I\':[\'eⁿ\',q.W,q.4n,\'1A 4o\',\'6J\',\'E\'],\'6K\':[\'x²\',q.W,q.4p,\'1A 6L\',\'6M\',\'@\'],\'6N\':[\'√\',q.W,q.4q,\'1A 4r\',\'6O\',\'!\'],\'6P\':[\'x^y\',q.1s,q.4s,\'1A 6Q\',\'6R\',\'^\'],\'6S\':[\'6T\',q.W,q.4t,\'4u\',\'6U\',\'?\'],\'6V\':[\'3j\',q.W,q.4v,\'1W 3j\',\'6W\',\'s\'],\'6X\':[\'3k\',q.W,q.4w,\'1W 3k\',\'6Y\',\'o\'],\'6Z\':[\'3l\',q.W,q.4x,\'1W 3l\',\'70\',\'t\'],\'71\':[\'3m\',q.W,q.4y,\'1W 3m\',\'72\',\'S\'],\'73\':[\'3n\',q.W,q.4z,\'1W 3n\',\'74\',\'O\'],\'75\':[\'3o\',q.W,q.4A,\'1W 3o\',\'76\',\'T\'],\'4B\':[\'#77\',q.W,q.4C,\'15 1I-2h\',\'78\',\'x\'],\'4D\':[\'#79\',q.W,q.4E,\'15 1I-7a\',\'7b\',\'r\'],\'4F\':[\'#7c\',q.W,q.4G,\'15 1I-7d\',\'7e\',\'m\'],\'M+\':[\'#7f\',q.W,q.4H,\'15 1I-4c\',\'7g\',\'>\'],\'M-\':[\'#7h\',q.W,q.4I,\'15 1I-4d\',\'7i\',\'<\'],\'7j\':[\'#4J\',q.1b,q.4K,\'1a 4J\',\'7k\',\'B\'],\'7l\':[\'#4L\',q.1b,q.4M,\'1a 4L\',\'7m\',\'C\'],\'7n\':[\'#4N\',q.1b,q.4O,\'1a 4N\',\'7o\',\'D\'],\'7p\':[\'#4P\',q.1b,q.4Q,\'1a 4P\',\'7q\',\'H\'],\'7r\':[\'#2B\',q.1b,q.4R,\'2C 2B\',\'7s\',\'G\'],\'7t\':[\'#2D\',q.1b,q.4S,\'2C 2D\',\'7u\',\'R\'],\'4T\':[\'#7v\',q.1b,q.4U,\'7w\',\'7x\',8,\'7y\'],\'4V\':[\'#7z\',q.1b,q.4W,\'2h-7A\',\'7B\',36,\'7C\'],\'4X\':[\'#2h\',q.1b,q.4Y,\'2h\',\'7D\',35,\'7E\'],\'@X\':[\'#4Z\',q.1b,q.3p,\'4Z\',\'7F\',27,\'7G\'],\'@U\':[\'#50\',q.1b,q.51,\'50\',\'7H\',13,\'7I\'],\'@E\':[\'#52\',q.1b,q.3q,\'52\',\'7J\',46,\'7K\'],\'  \':[\'\',q.1Y,L,\'1Y\',\'7L\'],\'14 \':[\'\',q.1Y,L,\'7M-1Y\',\'7N\'],\'??\':[\'??\',q.W,q.1B]};q.2E={};q.2F={};2i(z a 3r q.1k){I(q.1k[a][4]){q[q.1k[a][4]]=a}I(q.1k[a][5]){I(2j q.1k[a][5]==\'3s\'){q.2E[q.1k[a][5]]=a}17{q.2F[q.1k[a][5]]=a}}}q.3t=[];q.3t[\'\']={1Z:\'.\',53:\'...\',54:\'7O 1p v\',7P:\'55\',7Q:\'55 1p v\',7R:\'56\',7S:\'56 1p 7T 20\',7U:\'2G\',7V:\'2G 1p 20 3u 1p 7W\',7X:\'4T\',7Y:\'2G 1p 3v V\',7Z:\'4V\',80:\'2G 1p 3v 3s\',81:\'4X\',82:\'83 1p v\',84:\'4B\',85:\'57 1p 15\',86:\'4D\',87:\'58 1p 20 3u 15\',88:\'4F\',89:\'8a 1p 20 3r 15\',8b:\'M+\',8c:\'8d 1J 15\',8e:\'M-\',8f:\'8g 3u 15\',8h:\'8i\',8j:\'21 1J 1s\',8k:\'8l\',8m:\'21 1J 8n\',8o:\'8p\',8q:\'21 1J 4b\',8r:\'8s\',8t:\'21 1J 8u\',8v:\'8w\',8x:\'21 1J 2B\',8y:\'8z\',8A:\'21 1J 2D\',2k:11};q.2H={3w:\'1t\',59:\'\',5a:11,5b:L,3x:\'2I\',3y:{},3z:\'3A\',5c:\'\',5d:\'\',3B:\'\',5e:q.5f,20:0,1a:10,5g:10,2l:11,5h:12,5i:L,5j:L};$.2J(q.2H,q.3t[\'\']);q.2K=$(\'<19 8B="\'+q.3C+\'" 3D="3E: 5k;"></19>\').1K(q.5l)}$.2J(2d.5m,{1C:\'8C\',V:\'d\',1s:\'b\',W:\'u\',1b:\'c\',1Y:\'s\',3C:\'v-19\',2L:\'v-8D\',3F:\'v-2M\',1D:\'v-8E\',3G:\'v-1l\',2m:\'v-8F\',3H:\'v-5n\',2N:\'v-8G\',2O:\'v-22\',2P:\'v-8H\',5f:[\'  5o\',\'5p+@X\',\'5q-@U\',\'5r*@E\',\'5s.14=14/\'],8I:[\'@X@U@E  5o\',\'8J    14 8K 5r+\',\'8L 8M 5q-\',\'8N 8O 5p*\',\'8P M+14 5s.+-14/\',\'8Q  14 M-14   14%14=\'],8R:w(a){3I(q.2H,a||{});N q},8S:w(a,b,c,d,e,f,g,h){q.1k[a]=[b,(2j c==\'8T\'?(c?q.1s:q.W):c),d,e,f,g,h];I(f){q[f]=a}I(g){I(2j g==\'3s\'){q.2E[g]=a}17{q.2F[g]=a}}N q},5t:w(a,b){z c=$(a);z d=a.3J.2n()!=\'2Q\';z e=(!d?c:$(\'<2Q 2o="2R" 1f="\'+q.2m+\'"/>\'));z f={Q:e,1g:d,P:(d?$(\'<19 1f="\'+q.2L+\'"></19>\'):q.2K)};f.1L=$.2J({},b||{});q.5u(a,f);I(d){c.2M(e).2M(f.P).3K(\'1K.v\',w(){e.1t()});q.2p(f,\'0\',12);q.3L(f);q.1i(f)}},5u:w(d,e){z f=$(d);I(f.23(q.1C)){N}z g=q.K(e,\'5c\');z h=q.K(e,\'2k\');I(g){f[h?\'5v\':\'5w\'](\'<1u 1f="\'+q.3F+\'">\'+g+\'</1u>\')}I(!e.1g){z i=q.K(e,\'3w\');I(i==\'1t\'||i==\'3M\'){f.1t(q.24)}I(i==\'1c\'||i==\'3M\'||i==\'5x\'){z j=q.K(e,\'53\');z k=q.K(e,\'54\');z l=q.K(e,\'59\');z m=$(q.K(e,\'5a\')?$(\'<2S/>\').2q({3N:l,8U:k,3O:k}):$(\'<1c 2o="1c" 3O="\'+k+\'"></1c>\').5y(l==\'\'?j:$(\'<2S/>\').2q({3N:l})));f[h?\'5v\':\'5w\'](m);m.2r(q.1D).1K(w(){I($.v.1j&&$.v.2T==d){$.v.1M()}17{$.v.24(d)}N 11})}}e.Q.3P(q.2U).3Q(q.2V).3R(q.2W);I(e.1g){e.P.3P(q.2U).3Q(q.2V).3R(q.2W);e.Q.1t(w(){I(!$.v.2s(f[0])){e.3S=12;$(\'.\'+$.v.3H,e.P).2r($.v.2N)}}).5z(w(){e.3S=11;$(\'.\'+$.v.3H,e.P).2t($.v.2N)})}f.2r(q.1C).3K("8V.v",w(a,b,c){e.1L[b]=c}).3K("8W.v",w(a,b){N q.K(e,b)});$.1x(d,p,e);$.1x(e.Q[0],p,e)},8X:w(a){z b=$(a);I(!b.23(q.1C)){N}z c=$.1x(a,p);c.Q.2u(\'3P\',q.2U).2u(\'3Q\',q.2V).2u(\'3R\',q.2W);b.25(\'.\'+q.3F).2X().1N().25(\'.\'+q.1D).2X().1N().8Y(\'.\'+q.2m).2X().1N().2t(q.1C).2u(\'1t\',q.24).2u(\'1K.v\').5A();$.5B(c.Q[0],p);$.5B(a,p)},8Z:w(b){z c=$(b);I(!c.23(q.1C)){N}z d=b.3J.2n();I(d==\'2Q\'){b.1l=11;c.25(\'1c.\'+q.1D).26(w(){q.1l=11}).1N().25(\'2S.\'+q.1D).1m({5C:\'1.0\',5D:\'\'})}17 I(d==\'19\'||d==\'1u\'){c.1E(\'.\'+q.2m+\',1c\').2q(\'1l\',\'\').1N().3T(\'.\'+q.3G).2X()}q.1z=$.5E(q.1z,w(a){N(a==b?L:a)})},90:w(b){z c=$(b);I(!c.23(q.1C)){N}z d=b.3J.2n();I(d==\'2Q\'){b.1l=12;c.25(\'1c.\'+q.1D).26(w(){q.1l=12}).1N().25(\'2S.\'+q.1D).1m({5C:\'0.5\',5D:\'91\'})}17 I(d==\'19\'||d==\'1u\'){z e=c.3T(\'.\'+q.2L);z f=e.3U();z g={1h:0,1d:0};e.2Y().26(w(){I($(q).1m(\'2Z\')==\'92\'){g=$(q).3U();N 11}});c.1E(\'.\'+q.2m+\',1c\').2q(\'1l\',\'1l\').1N().93(\'<19 1f="\'+q.3G+\'" 3D="1O: \'+e.28()+\'29; 3V: \'+e.2v()+\'29; 1h: \'+(f.1h-g.1h)+\'29; 1d: \'+(f.1d-g.1d)+\'29;"></19>\')}q.1z=$.5E(q.1z,w(a){N(a==b?L:a)});q.1z[q.1z.1P]=b},2s:w(a){N(a&&$.94(a,q.1z)>-1)},95:w(a,b,c){z d=b||{};I(2j b==\'5F\'){d={};d[b]=c}z e=$.1x(a,p);I(e){I(q.1o==e){q.1M()}3I(e.1L,d);I(e.1g){q.3L(e)}q.1i(e)}},24:w(b){b=b.1Q||b;I($.v.2s(b)||$.v.2T==b){N}z c=$.1x(b,p);$.v.1M(L,\'\');$.v.2T=b;$.v.1R=$.v.3W(b);$.v.1R[1]+=b.96;z d=11;$(b).2Y().26(w(){d|=$(q).1m(\'2Z\')==\'5G\';N!d});I(d&&$.1v.2w){$.v.1R[0]-=1q.1F.30;$.v.1R[1]-=1q.1F.31}z e={1h:$.v.1R[0],1d:$.v.1R[1]};$.v.1R=L;c.P.1m({2Z:\'5H\',3E:\'97\',1d:\'-5I\',1O:($.1v.2w?\'5I\':\'98\')});$.v.2p(c,c.Q.2a(),12);$.v.1i(c);e=$.v.5J(c,e,d);c.P.1m({2Z:(d?\'5G\':\'5H\'),3E:\'5k\',1h:e.1h+\'29\',1d:e.1d+\'29\'});z f=$.v.K(c,\'3x\');z g=$.v.K(c,\'3z\');g=(g==\'3A\'&&$.32&&$.32.33>=\'1.8\'?\'5K\':g);z h=w(){$.v.1j=12;z a=$.v.3X(c.P);c.P.1E(\'34.\'+$.v.2P).1m({1h:-a[0],1d:-a[1],1O:c.P.28(),3V:c.P.2v()})};I($.37&&$.37[f]){c.P.2I(f,$.v.K(c,\'3y\'),g,h)}17{c.P[f||\'2I\']((f?g:\'\'),h)}I(!f){h()}I(c.Q[0].2o!=\'5L\'){c.Q[0].1t()}$.v.1o=c},2p:w(a,b,c){z d=q.K(a,\'1a\');z e=q.K(a,\'1Z\');b=\'\'+(b||0);b=(e!=\'.\'?b.1r(1G 2x(e),\'.\'):b);a.J=(d==10?2b(b):1S(b,d))||0;a.Y=q.1T(a);a.1n=a.3Y=0;a.15=(c?0:a.15);a.1e=a.2y=q.1B;a.1y=12},3L:w(a){a.J=q.K(a,\'20\')||0;a.Y=q.1T(a)},1i:w(a){z b=q.3X(a.P);a.P.5y(q.5M(a)).1E(\'34.\'+q.2P).1m({1h:-b[0],1d:-b[1],1O:a.P.28(),3V:a.P.2v()});a.P.2t().2r(q.K(a,\'5d\')+\' \'+(q.K(a,\'2k\')?\'v-99 \':\'\')+(a.1g?q.2L:\'\'));I(q.1o==a){a.Q.1t()}},3X:w(c){z d=w(a){z b=($.1v.3Z?1:0);N{9a:1+b,9b:3+b,9c:5+b}[a]||a};N[2b(d(c.1m(\'5N-1h-1O\'))),2b(d(c.1m(\'5N-1d-1O\')))]},5J:w(a,b,c){z d=a.Q?q.3W(a.Q[0]):L;z e=5O.9d||1q.1F.9e;z f=5O.9f||1q.1F.9g;z g=1q.1F.30||1q.40.30;z h=1q.1F.31||1q.40.31;I(($.1v.3Z&&1S($.1v.33,10)<7)||$.1v.2w){z i=0;$(\'.v-5P\',a.P).1E(\'1c:3v\').26(w(){i=Z.41(i,q.9h+q.9i+1S($(q).1m(\'9j-9k\'),10))});a.P.1m(\'1O\',i)}I(q.K(a,\'2k\')||(b.1h+a.P.28()-g)>e){b.1h=Z.41((c?0:g),d[0]+(a.Q?a.Q.28():0)-(c?g:0)-a.P.28()-(c&&$.1v.2w?1q.1F.30:0))}17{b.1h-=(c?g:0)}I((b.1d+a.P.2v()-h)>f){b.1d=Z.41((c?0:h),d[1]-(c?h:0)-a.P.2v()-(c&&$.1v.2w?1q.1F.31:0))}17{b.1d-=(c?h:0)}N b},3W:w(a){9l(a&&(a.2o==\'5L\'||a.9m!=1)){a=a.9n}z b=$(a).3U();N[b.1h,b.1d]},1M:w(a,b){z c=q.1o;I(!c||(a&&c!=$.1x(a,p))){N}I(q.1j){b=(b!=L?b:q.K(c,\'3z\'));b=(b==\'3A\'&&$.32&&$.32.33>=\'1.8\'?\'5K\':b);z d=q.K(c,\'3x\');I($.37&&$.37[d]){c.P.42(d,q.K(c,\'3y\'),b)}17{c.P[(d==\'9o\'?\'9p\':(d==\'9q\'?\'9r\':\'42\'))](d?b:\'\')}}z e=q.K(c,\'5j\');I(e){e.1U((c.Q?c.Q[0]:L),[(c.1g?c.J:c.Q.2a()),c])}I(q.1j){q.1j=11;q.2T=L}q.1o=L},5Q:w(a){I(!$.v.1o){N}z b=$(a.1Q);I(!b.2Y().5R().9s(\'#\'+$.v.3C)&&!b.23($.v.1C)&&!b.2Y().5R().23($.v.1D)&&$.v.1j){$.v.1M(L,\'\')}},5l:w(){I($.v.1o&&$.v.1o.Q){$.v.1o.Q.1t()}},2U:w(e){z a=11;z b=$.1x(e.1Q,p);z c=(b&&b.1g?$(e.1Q).5S()[0]:L);I(e.2z==9){$.v.2K.9t(12,12);$.v.1M(L,\'\');I(b&&b.1g){b.Q.5z()}}17 I($.v.1j||(c&&!$.v.2s(c))){I(e.2z==18){I(!$.v.2e){b.P.1E(\'.\'+$.v.2O).2I();$.v.2e=12}a=12}17{z d=$.v.2E[e.2z];I(d){$(\'1c[22=\'+d+\']\',b.P).5T(\':1l\').1K();a=12}}}17 I(e.2z==36&&e.9u&&b&&!b.1g){$.v.24(q)}I(a){e.9v();e.9w()}N!a},2V:w(e){I($.v.2e){z a=$.1x(e.1Q,p);a.P.1E(\'.\'+$.v.2O).42();$.v.2e=11}},2W:w(e){z a=$.1x(e.1Q,p);I(!a){N 12}z b=(a&&a.1g?$(e.1Q).5S()[0]:L);z c=9x.9y(e.5U==43?e.2z:e.5U);z d=$.v.K(a,\'1a\');z f=$.v.K(a,\'1Z\');z g=$.v.K(a,\'3w\');z h=$.v.K(a,\'5b\')||$.v.5V;I(!$.v.1j&&!b&&(g==\'9z\'||g==\'5x\')&&h.1U(a.Q,[c,e,a.Q.2a(),d,f])){$.v.24(q);$.v.1j=12}I($.v.1j||(b&&!$.v.2s(b))){z i=$.v.2F[c==f?\'.\':c];I(i){$(\'1c[22=\'+i+\']\',a.P).5T(\':1l\').1K()}N 11}I(c>=\' \'&&$.v.K(a,\'5h\')){z j=1G 2x(\'^-?\'+(d==10?\'[0-9]*(\\\\\'+f+\'[0-9]*)?\':\'[\'+\'5W\'.9A(0,d)+\']*\')+\'$\');N(a.Q.2a()+c).2n().5X(j)!=L}N 12},5V:w(a,b,c,d,e){N a>\' \'&&!(a==\'-\'&&c==\'\')&&(\'5W\'.2c(0,d)+\'.\'+e).5Y(a.2n())==-1},K:w(a,b){N a.1L[b]!==43?a.1L[b]:q.2H[b]},5M:w(a){z b=q.K(a,\'2k\');z c=q.K(a,\'3B\');z d=q.K(a,\'5e\');z e=q.K(a,\'1a\');z f=q.K(a,\'2l\');z g=(!c?\'\':\'<19 1f="v-3B">\'+c+\'</19>\')+\'<19 1f="v-5n\'+(a.3S?\' \'+q.2N:\'\')+\'"><1u>\'+a.Y+\'</1u></19>\';2i(z i=0;i<d.1P;i++){g+=\'<19 1f="v-5P">\';2i(z j=0;j<d[i].1P;j+=2){z h=d[i].2c(j,2);z l=q.1k[h]||q.1k[\'??\'];z m=(l[0].5Z(0)==\'#\'?q.K(a,l[0].2c(1)+\'9B\'):l[0]);z n=(l[0].5Z(0)==\'#\'?q.K(a,l[0].2c(1)+\'9C\'):\'\');z o=(l[3]?l[3].9D(\' \'):[]);2i(z k=0;k<o.1P;k++){o[k]=\'v-\'+o[k]}o=o.9E(\' \');g+=(l[1]==q.1Y?\'<1u 1f="v-\'+l[3]+\'"></1u>\':(a.1g&&(l[2]==\'.3p\'||l[2]==\'.3q\')?\'\':\'<1c 2o="1c" 22="\'+h+\'"\'+(l[1]==q.1b?\' 1f="v-9F\'+(l[0].1r(/^#1a/,\'\')==e?\' v-1a-44\':\'\')+(l[0]==\'#2B\'&&f?\' v-2C-44\':\'\')+(l[0]==\'#2D\'&&!f?\' v-2C-44\':\'\'):(l[1]==q.V?(1S(l[0],16)>=e||(e!=10&&l[0]==\'.\')?\' 1l="1l"\':\'\')+\' 1f="v-V\':(l[1]==q.1s?\' 1f="v-60\':\' 1f="v-60\'+(l[0].5X(/^#1I(57|58)$/)&&!a.15?\' v-1I-5A\':\'\'))))+(o?\' \'+o:\'\')+\'" \'+(n?\'3O="\'+n+\'"\':\'\')+\'>\'+(h==\'14.\'?q.K(a,\'1Z\'):m)+(l[5]&&l[5]!=l[0]?\'<1u 1f="\'+q.2O+(l[6]?\' v-9G\':\'\')+\'">\'+(l[6]||l[5])+\'</1u>\':\'\')+\'</1c>\'))}g+=\'</19>\'}g+=\'<19 3D="2h: 3M;"></19>\'+(!a.1g&&$.1v.3Z&&1S($.1v.33,10)<7?\'<34 3N="9H:11;" 1f="\'+q.2P+\'"></34>\':\'\');g=$(g);g.1E(\'1c\').61(w(){$(q).2r(\'v-45-47\')}).9I(w(){$(q).2t(\'v-45-47\')}).9J(w(){$(q).2t(\'v-45-47\')}).1K(w(){$.v.62(a,$(q))});N g},1T:w(a){z b=q.K(a,\'5g\');z c=1G 63(a.J).64(b).65();z d=c.1r(/^.+(e.+)$/,\'$1\').1r(/^[^e].*$/,\'\');I(d){c=1G 63(c.1r(/e.+$/,\'\')).64(b).65()}N 2b(c.1r(/0+$/,\'\')+d).9K(q.K(a,\'1a\')).9L().1r(/\\./,q.K(a,\'1Z\'))},1w:w(a,b){z c=q.K(a,\'5i\');I(c){c.1U((a.Q?a.Q[0]:L),[b,a.Y,a])}},62:w(a,b){z c=q.1k[b.2q(\'22\')];I(!c){N}z d=b.2R().2c(0,b.2R().1P-b.3T(\'.v-22\').2R().1P);9M(c[1]){38 q.1b:c[2].1U(q,[a,d]);39;38 q.V:q.66(a,d);39;38 q.1s:q.67(a,c[2],d);39;38 q.W:q.48(a,c[2],d);39}I($.v.1j||a.1g){a.Q.1t()}},1B:w(a){},66:w(a,b){z c=q.K(a,\'1Z\');a.Y=(a.1y?\'\':a.Y);I(b==c&&a.Y.5Y(b)>-1){N}a.Y=(a.Y+b).1r(/^0(\\d)/,\'$1\').1r(1G 2x(\'^(-?)([\\\\.\'+c+\'])\'),\'$10$2\');I(c!=\'.\'){a.Y=a.Y.1r(1G 2x(\'^\'+c),\'0.\')}z d=q.K(a,\'1a\');z e=(c!=\'.\'?a.Y.1r(1G 2x(c),\'.\'):a.Y);a.J=(d==10?2b(e):1S(e,d));a.1y=11;q.1w(a,b);q.1i(a)},67:w(a,b,c){I(!a.1y&&a.1e){a.1e(a);z d=q.K(a,\'1a\');a.J=(d==10?a.J:Z.49(a.J));a.Y=q.1T(a)}a.1n=a.J;a.1y=12;a.1e=b;q.1w(a,c);q.1i(a)},3e:w(a){a.J=a.1n+a.J},3f:w(a){a.J=a.1n-a.J},3g:w(a){a.J=a.1n*a.J},3h:w(a){a.J=a.1n/a.J},4s:w(a){a.J=Z.9N(a.1n,a.J)},48:w(a,b,c){a.1y=12;b.1U(q,[a]);z d=q.K(a,\'1a\');a.J=(d==10?a.J:Z.49(a.J));a.Y=q.1T(a);q.1w(a,c);q.1i(a)},4f:w(a){a.J=-1*a.J;a.Y=q.1T(a);a.1y=11},4h:w(a){a.J=Z.2f},4e:w(a){I(a.1e==q.3e){a.J=a.1n*(1+a.J/3a)}17 I(a.1e==q.3f){a.J=a.1n*(1-a.J/3a)}17 I(a.1e==q.3g){a.J=a.1n*a.J/3a}17 I(a.1e==q.3h){a.J=a.1n/a.J*3a}a.2y=a.1e;a.1e=q.1B},3i:w(a){I(a.1e==q.1B){I(a.2y!=q.1B){a.1n=a.J;a.J=a.3Y;a.2y(a)}}17{a.2y=a.1e;a.3Y=a.J;a.1e(a);a.1e=q.1B}},4H:w(a){a.15+=a.J},4I:w(a){a.15-=a.J},4G:w(a){a.15=a.J},4E:w(a){a.J=a.15},4C:w(a){a.15=0},4v:w(a){q.3b(a,Z.3j)},4w:w(a){q.3b(a,Z.3k)},4x:w(a){q.3b(a,Z.3l)},3b:w(a,b){z c=q.K(a,\'2l\');a.J=b(a.J*(c?Z.2f/68:1))},4y:w(a){q.3c(a,Z.3m)},4z:w(a){q.3c(a,Z.3n)},4A:w(a){q.3c(a,Z.3o)},3c:w(a,b){a.J=b(a.J);I(q.K(a,\'2l\')){a.J=a.J/Z.2f*68}},4i:w(a){a.J=1/a.J},4j:w(a){a.J=Z.2g(a.J)/Z.2g(10)},4m:w(a){a.J=Z.2g(a.J)},4n:w(a){a.J=Z.4o(a.J)},4p:w(a){a.J*=a.J},4q:w(a){a.J=Z.4r(a.J)},4t:w(a){a.J=Z.4u()},4K:w(a,b){q.2A(a,b,2)},4M:w(a,b){q.2A(a,b,8)},4O:w(a,b){q.2A(a,b,10)},4Q:w(a,b){q.2A(a,b,16)},2A:w(a,b,c){a.1L.1a=c;a.J=(c==10?a.J:Z.49(a.J));a.Y=q.1T(a);a.1y=12;q.1w(a,b);q.1i(a)},4R:w(a,b){q.4a(a,b,12)},4S:w(a,b){q.4a(a,b,11)},4a:w(a,b,c){a.1L.2l=c;q.1w(a,b);q.1i(a)},4U:w(a,b){a.Y=a.Y.2c(0,a.Y.1P-1)||\'0\';z c=q.K(a,\'1a\');a.J=(c==10?2b(a.Y):1S(a.Y,c));q.1w(a,b);q.1i(a)},4W:w(a,b){a.Y=\'0\';a.J=0;a.1y=12;q.1w(a,b);q.1i(a)},4Y:w(a,b){q.2p(a,0,11);q.1w(a,b);q.1i(a)},3p:w(a,b){q.3d(a,b,a.Q.2a())},51:w(a,b){I(a.1e!=q.1B){q.48(a,q.3i,b)}q.3d(a,b,a.Y)},3q:w(a,b){q.2p(a,0,11);q.1i(a);q.3d(a,b,\'\')},3d:w(a,b,c){I(a.1g){q.1o=a}17{a.Q.2a(c)}q.1w(a,b);q.1M(a.Q[0])}});w 3I(a,b){$.2J(a,b);2i(z c 3r b){I(b[c]==L||b[c]==43){a[c]=b[c]}}N a};$.1A.v=w(a){z b=9O.5m.9P.9Q(9R,1);I(a==\'9S\'){N $.v[\'14\'+a+\'2d\'].1U($.v,[q[0]].69(b))}N q.26(w(){2j a==\'5F\'?$.v[\'14\'+a+\'2d\'].1U($.v,[q].69(b)):$.v.5t(q,a)})};$.v=1G 2d();$(w(){$(1q.40).2M($.v.2K).61($.v.5Q)})})(9T);',62,614,'||||||||||||||||||||||||||this|||||calculator|function|||var|||||||||if|curValue|_get|null||return||_mainDiv|_input|||||digit|unary||dispValue|Math||false|true||_|memory||else||div|base|control|button|top|_pendingOp|class|_inline|left|_updateCalculator|_showingCalculator|_keyDefs|disabled|css|prevValue|_curInst|the|document|replace|binary|focus|span|browser|_sendButton|data|_newValue|_disabledFields|fn|_noOp|markerClassName|_triggerClass|find|documentElement|new|arith|mem|to|click|settings|_hideCalculator|end|width|length|target|_pos|parseInt|_setDisplay|apply|hex|trig||space|decimalChar|value|Switch|keystroke|hasClass|_showCalculator|siblings|each||outerWidth|px|val|parseFloat|substr|Calculator|_showingKeystrokes|PI|log|clear|for|typeof|isRTL|useDegrees|_inlineEntryClass|toLowerCase|type|_reset|attr|addClass|_isDisabledCalculator|removeClass|unbind|outerHeight|opera|RegExp|_savedOp|keyCode|_changeBase|degrees|angle|radians|_keyCodes|_keyChars|Erase|_defaults|show|extend|mainDiv|_inlineClass|append|_focussedClass|_keystrokeClass|_coverClass|input|text|img|_lastInput|_doKeyDown|_doKeyUp|_doKeyPress|remove|parents|position|scrollLeft|scrollTop|ui|version|iframe|||effects|case|break|100|_trig|_atrig|_finished|_add|_subtract|_multiply|_divide|_equals|sin|cos|tan|asin|acos|atan|_close|_erase|in|number|regional|from|last|showOn|showAnim|showOptions|duration|normal|prompt|_mainDivId|style|display|_appendClass|_disableClass|_resultClass|extendRemove|nodeName|bind|_setValue|both|src|title|keydown|keyup|keypress|_focussed|children|offset|height|_findPos|_getBorders|_savedValue|msie|body|max|hide|undefined|active|key||down|_unaryOp|floor|_degreesRadians|decimal|add|subtract|_percent|_plusMinus|pi|_pi|_inverse|_log|LN|ln|_ln|_exp|exp|_sqr|_sqrt|sqrt|_power|_random|random|_sin|_cos|_tan|_asin|_acos|_atan|MC|_memClear|MR|_memRecall|MS|_memStore|_memAdd|_memSubtract|base2|_base2|base8|_base8|base10|_base10|base16|_base16|_degrees|_radians|BS|_undo|CE|_clearError|CA|_clear|close|use|_use|erase|buttonText|buttonStatus|Close|Use|Clear|Recall|buttonImage|buttonImageOnly|isOperator|appendText|calculatorClass|layout|standardLayout|precision|constrainInput|onButton|onClose|none|_focusEntry|prototype|result|BSCECA|_1_2_3_|_4_5_6_|_7_8_9_|_0_|_attachCalculator|_connectCalculator|before|after|opbutton|html|blur|empty|removeData|opacity|cursor|map|string|fixed|absolute|1000px|_checkOffset|_default|hidden|_generateHTML|border|window|row|_checkExternalClick|andSelf|parent|not|charCode|_isOperator|0123456789abcdef|match|indexOf|charAt|oper|mousedown|_handleButton|Number|toFixed|valueOf|_digit|_binaryOp|180|concat|_0|_1|_2|_3|_4|_5|_6|_7|_8|_9|_A|_B|_C|_D|_E|_F|DECIMAL|ADD|SUBTRACT|multiply|MULTIPLY|divide|DIVIDE|percent|PERCENT|equals|EQUALS|plus|minus|PLUS_MINUS|inverse|INV|LG|LOG|EX|EXP|SQ|sqr|SQR|SR|SQRT|XY|power|POWER|RN|rnd|RANDOM|SN|SIN|CS|COS|TN|TAN|AS|ASIN|AC|ACOS|AT|ATAN|memClear|MEM_CLEAR|memRecall|recall|MEM_RECALL|memStore|store|MEM_STORE|memAdd|MEM_ADD|memSubtract|MEM_SUBTRACT|BB|BASE_2|BO|BASE_8|BD|BASE_10|BH|BASE_16|DG|DEGREES|RD|RADIANS|backspace|undo|UNDO|BSp|clearError|error|CLEAR_ERROR|Hom|CLEAR|End|CLOSE|Esc|USE|Ent|ERASE|Del|SPACE|half|HALF_SPACE|Open|closeText|closeStatus|useText|useStatus|current|eraseText|eraseStatus|field|backspaceText|backspaceStatus|clearErrorText|clearErrorStatus|clearText|clearStatus|Reset|memClearText|memClearStatus|memRecallText|memRecallStatus|memStoreText|memStoreStatus|Store|memAddText|memAddStatus|Add|memSubtractText|memSubtractStatus|Subtract|base2Text|Bin|base2Status|base8Text|Oct|base8Status|octal|base10Text|Dec|base10Status|base16Text|Hex|base16Status|hexadecimal|degreesText|Deg|degreesStatus|radiansText|Rad|radiansStatus|id|hasCalculator|inline|trigger|keyentry|focussed|cover|scientificLayout|DGRD|MC_|SNASSRLG_|MR_|CSACSQLN_|MS_|TNATXYEX_|PIRN1X|setDefaults|addKeyDef|boolean|alt|setData|getData|_destroyCalculator|prev|_enableCalculator|_disableCalculator|default|relative|prepend|inArray|_changeCalculator|offsetHeight|block|auto|rtl|thin|medium|thick|innerWidth|clientWidth|innerHeight|clientHeight|offsetLeft|offsetWidth|margin|right|while|nodeType|nextSibling|slideDown|slideUp|fadeIn|fadeOut|is|stop|ctrlKey|preventDefault|stopPropagation|String|fromCharCode|operator|substring|Text|Status|split|join|ctrl|keyname|javascript|mouseup|mouseout|toString|toUpperCase|switch|pow|Array|slice|call|arguments|isDisabled|jQuery'.split('|'),0,{}))