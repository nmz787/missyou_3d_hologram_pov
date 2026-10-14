
        (function() {
            var s = '{{TEXT}}';
            const platform = "{{PLATFORM}}";
            var obox = document.getElementById('drag-container');
            document.body.addEventListener("touchstart", () => { });

            function setCss3(obj, attrObj) {
                for (var i in attrObj) {
                    var newi = i;
                    if (newi.indexOf("-") > 0) {
                        var num = newi.indexOf("-");
                        newi = newi.replace(newi.substr(num, 2), newi.substr(num + 1, 1).toUpperCase());
                    }
                    obj.style[newi] = attrObj[i];
                    newi = newi.replace(newi.charAt(0), newi.charAt(0).toUpperCase());
                    obj.style["webkit" + newi] = attrObj[i];
                    obj.style["moz" + newi] = attrObj[i];
                    obj.style["o" + newi] = attrObj[i];
                    obj.style["ms" + newi] = attrObj[i];
                }
            }

            var middle = document.getElementsByClassName('middle')[0];
            var oUl = middle.getElementsByTagName('ul')[0];
            var oDiv = middle.getElementsByTagName('div')[1];
            var aLi = oUl.getElementsByTagName('li');
            var r = document.getElementById("box").offsetWidth / 2;
            var circleArr = [];
            var coneArr = [];
            var coneNum = 0;
            var wordNum = -1;
            var liNub = 0;
            var theta = 0;
            var phi = 0;
            var layer = 0;
            var num = 0;
            var iTimer2 = 0;
            var columnH = 0;
            var columnNum = 0;
            var iTimer;
            var angleX = 0;
            var angleY = 0;

            initAnimation();

            function initAnimation() {
                document.getElementById("box").style.height = document.getElementById("box").offsetWidth + "px";//设置宽高比为1:1
                r = document.getElementById("box").offsetWidth / 2;
                start();

                iTimer = setInterval(function () {
                    //angleX -= 3;
                    angleY -= 1.8;
                    tX = angleY; // 保持一致
                    // setCss3(oDiv, { transform: 'rotateX(' + angleX + 'deg) rotateY(' + angleY + 'deg)' });
                    applyTransform(obox);
                }, 50);
            }

            function start() {
                circleArr = [];
                coneArr = [];
                coneNum = 0;
                wordNum = -3;
                liNub = 0;
                theta = 0;
                phi = 0;
                layer = 0;
                num = 0;
                var ss = new Array();
                var as = new Array();
                as.push(...s);
                ss.push(...as);

                while (ss.length < 170) {
                    ss.push(...as);
                }

                for (var i = 3; i < 13; i++) {
                    num = 2 * i * i + 3 * i;
                    num = 2 * num - 4 * i - 1;

                    if (num > ss.length) {
                        layer = 2 * i - 3;
                        break;
                    }

                    layer = 2 * i - 3;
                }

                var dpr = window.devicePixelRatio || 1;
                var swidth = document.getElementById("box").offsetWidth;
                var size = swidth / layer * dpr / 2.5;
                console.log("box宽度 swidth:", swidth);
                console.log("计算的layer:", layer);
                console.log("设备像素比 DPR =", dpr);

                for (var i = 0; i < layer + 1; i++) {
                    if (i <= (layer + 1) / 2) {
                        wordNum += 4;
                    } else {
                        wordNum -= 4;
                    }
                    circleArr.push(wordNum);
                }

                num = 0;
                for (var i = 0; i < circleArr.length; i++) {
                    theta = Math.PI / circleArr.length;
                    phi = 2 * Math.PI / circleArr[i];
                    
                    for (var j = 0; j < circleArr[i]; j++) {
                        if (i > 0) {
                            var li = document.createElement('li');
                            li.style.opacity = '0';
                            li.innerHTML = ss[num];
                            li.style["line-height"] = size + "px";
                            li.style["font-size"] = size + "px";
                            li.style["margin-top"] = "0px";
                            li.style["margin-left"] = "0px";

                            // 背景和圆角
                            // li.style["background"] = "rgba(255,0,0,0.3)";
                            // li.style["border-radius"] = "4px";

                            if (ss[num].indexOf("<img") >= 0) {
                                var img = li.getElementsByTagName("img")[0];
                                img.width = size;
                                img.height = size;
                            }

                            num++;
                            drawCircle(li, theta, phi, i, j);
                            oUl.appendChild(li);
                        }
                    }
                }

                startChange();
            }

            function drawCircle(obj, theta, phi, i, j) {
                var x = r * Math.sin(theta * i) * Math.sin(phi * j);
                var y = -r * Math.cos(theta * i);
                var z = r * Math.sin(theta * i) * Math.cos(phi * j);
    
                obj.circleX = x + r;
                obj.circleY = y + r;
                obj.circleZ = z;

                // 保存初始球面坐标（不带 +r 偏移）
                obj.oriX = x;
                obj.oriY = y;
                obj.oriZ = z;

                obj.circleTheta = theta * (circleArr.length - i);
                obj.circlePhi = phi * j;
                obj.bigCircleX = (r + 2000) * Math.sin(theta * i) * Math.sin(phi * j) + r;
                obj.bigCircleY = -(r + 2000) * Math.cos(theta * i) + r;
                obj.bigCircleZ = (r + 2000) * Math.sin(theta * i) * Math.cos(phi * j);
                obj.maxX = obj.bigCircleX;
                obj.maxY = obj.bigCircleY;
                obj.maxZ = obj.bigCircleZ;
                obj.maxTheta = obj.circleTheta;
                obj.maxPhi = obj.circlePhi;
            }

            function startChange() {
                for (var i = 0; i < aLi.length; i++) {
                    aLi[i].className = 'one';
                }
                applyTransform(obox);
            }

            function rotatePoint(x, y, z, rotYDeg, rotXDeg) {
                let radY = rotYDeg * Math.PI / 180; // 绕 Y 轴
                let radX = rotXDeg * Math.PI / 180; // 绕 X 轴

                // 绕 Y 轴旋转
                let x1 = x * Math.cos(radY) + z * Math.sin(radY);
                let z1 = -x * Math.sin(radY) + z * Math.cos(radY);

                // 绕 X 轴旋转
                let y1 = y * Math.cos(radX) - z1 * Math.sin(radX);
                let z2 = y * Math.sin(radX) + z1 * Math.cos(radX);

                return { x: x1, y: y1, z: z2 };
            }

            function updateLiOpacity(li, rotatedZ) {
                var opacity = (rotatedZ + r) / (2 * r);
                opacity = Math.max(0.2, Math.min(1, opacity));
                li.style.opacity = opacity;
            }

            var tX = 0;
            var tY = 0;
            function applyTransform(obj) {
                var radY = tX * Math.PI / 180;
                for (var i = 0; i < aLi.length; i++) {
                    var ox = aLi[i].oriX, oy = aLi[i].oriY, oz = aLi[i].oriZ;
                    var nx = ox * Math.cos(radY) + oz * Math.sin(radY);
                    var nz = -ox * Math.sin(radY) + oz * Math.cos(radY);
                    var opacity = (nz + r) / (2 * r);
                    aLi[i].style.opacity = Math.max(0.2, Math.min(1, opacity));
                    var newPhi = aLi[i].circlePhi + radY;
                    setCss3(aLi[i], { transform: 'translate(-50%,-50%) translate3D(' + (nx + r) + 'px,' + (oy + r) + 'px,' + nz + 'px) rotateY(' + newPhi + 'rad) rotateX(' + (aLi[i].circleTheta - Math.PI / 2) + 'rad)' });
                }
            }

            if (platform == "ios" || platform == "android") {
                document.ontouchstart = function (e) {
                    e = e || window.event;
                    var sY = e.touches[0].clientY;
                    var sX = e.touches[0].clientX;
                    this.ontouchmove = function (e) {
                        e = e || window.event;
                        var nY = e.touches[0].clientY;
                        var nX = e.touches[0].clientX;
                        desY = nY - sY;
                        desX = nX - sX;
                        tY += desY * 0.1;
                        tX += desX * 0.1;
                        applyTransform(obox);
                        sY = nY;
                        sX = nX;
                    }
                    this.ontouchend = function (e) {
                    }
                }
            } else {
                document.onmousedown = function (e) {
                    e = e || window.event;
                    var sY = e.clientY;
                    var sX = e.clientX;

                    this.onmousemove = function (e) {
                        e = e || window.event;
                        var nY = e.clientY;
                        var nX = e.clientX;
                        desY = nY - sY;
                        desX = nX - sX;
                        tY += desY * 0.1;
                        tX += desX * 0.1;
                        applyTransform(obox);
                        sY = nY;
                        sX = nX;
                    }

                    this.onmouseup = function (e) {

                    }
                }
            }
            // ===== 导出接口 =====
            window.pauseAnimation=function(){clearInterval(iTimer);iTimer=null;};
            window.resumeAnimation=function(){if(!iTimer)iTimer=setInterval(function(){angleY-=1.8;tX=angleY;applyTransform(obox);},50);};
            window.getTotalSteps=function(){return 200;};

            window.exportFrames=function(totalSteps){
              try{
              clearInterval(iTimer);iTimer=null;
              var savedAngleY=angleY;
              angleY=0;tX=0;

              var eS=720;
              // 预览中 .box 宽度 = 80vw，球半径 r = box.offsetWidth/2 = 40vw
              // 导出 canvas 720px，等比缩放：exportBoxWidth = 720*0.8 = 576, eR = 576/2 = 288
              var exportBoxW=eS*0.8;
              var eR=exportBoxW/2;
              var scaleFactor=eR/r;

              // 从预览中获取实际字体大小，等比缩放到导出尺寸
              var previewFontSize=parseFloat(aLi[0]?aLi[0].style.fontSize:14);
              var exportFontSize=previewFontSize*scaleFactor;

              // ===== WebGL 离屏 canvas — 3D 球面文字 =====
              var ec=document.createElement('canvas');
              ec.width=eS;ec.height=eS;
              var gl2=ec.getContext('webgl',{preserveDrawingBuffer:true,antialias:true});
              gl2.viewport(0,0,eS,eS);

              // 着色器
              var evs='attribute vec3 aP;attribute vec4 aC;attribute vec2 aT;uniform mat4 uMVP;varying vec4 vC;varying vec2 vT;void main(){vC=aC;vT=aT;gl_Position=uMVP*vec4(aP,1.0);}';
              var efs='precision mediump float;varying vec4 vC;varying vec2 vT;uniform sampler2D uTex;uniform float uUseTex;void main(){if(uUseTex>0.5){vec4 tc=texture2D(uTex,vT);gl_FragColor=vec4(tc.rgb,vC.a*tc.a);}else{gl_FragColor=vC;}}';
              function mkSh(s,t){var sh=gl2.createShader(t);gl2.shaderSource(sh,s);gl2.compileShader(sh);return sh;}
              var pg2=gl2.createProgram();
              gl2.attachShader(pg2,mkSh(evs,gl2.VERTEX_SHADER));
              gl2.attachShader(pg2,mkSh(efs,gl2.FRAGMENT_SHADER));
              gl2.linkProgram(pg2);gl2.useProgram(pg2);
              var aP2=gl2.getAttribLocation(pg2,'aP'),aC2=gl2.getAttribLocation(pg2,'aC'),aT2=gl2.getAttribLocation(pg2,'aT');
              var uMVP2=gl2.getUniformLocation(pg2,'uMVP'),uTex2=gl2.getUniformLocation(pg2,'uTex'),uUseTex2=gl2.getUniformLocation(pg2,'uUseTex');

              // 矩阵工具
              function mulM2(a,b){var r=new Float32Array(16);for(var c=0;c<4;c++)for(var rr=0;rr<4;rr++){var s=0;for(var k=0;k<4;k++)s+=a[k*4+rr]*b[c*4+k];r[c*4+rr]=s;}return r;}

              // 为每个字符生成纹理
              // 纹理 canvas 大小要足够容纳字符，用 2 的幂次方便 GPU
              var charTexSize=128;
              var charCanvas=document.createElement('canvas');
              charCanvas.width=charTexSize;charCanvas.height=charTexSize;
              var charCtx=charCanvas.getContext('2d');
              var colorStr='{{COLOR}}';

              function makeCharTex(ch){
                charCtx.clearRect(0,0,charTexSize,charTexSize);
                charCtx.fillStyle=colorStr;
                // 纹理中字符占满整个纹理，实际显示大小由四边形尺寸控制
                charCtx.font=Math.floor(charTexSize*0.8)+'px sans-serif';
                charCtx.textAlign='center';
                charCtx.textBaseline='middle';
                charCtx.fillText(ch,charTexSize/2,charTexSize/2);
                var tex=gl2.createTexture();
                gl2.bindTexture(gl2.TEXTURE_2D,tex);
                gl2.texImage2D(gl2.TEXTURE_2D,0,gl2.RGBA,gl2.RGBA,gl2.UNSIGNED_BYTE,charCanvas);
                gl2.texParameteri(gl2.TEXTURE_2D,gl2.TEXTURE_MIN_FILTER,gl2.LINEAR);
                gl2.texParameteri(gl2.TEXTURE_2D,gl2.TEXTURE_MAG_FILTER,gl2.LINEAR);
                gl2.texParameteri(gl2.TEXTURE_2D,gl2.TEXTURE_WRAP_S,gl2.CLAMP_TO_EDGE);
                gl2.texParameteri(gl2.TEXTURE_2D,gl2.TEXTURE_WRAP_T,gl2.CLAMP_TO_EDGE);
                return tex;
              }

              // 收集文字数据并创建纹理
              var pts=[];
              for(var i=0;i<aLi.length;i++){
                var li=aLi[i];
                pts.push({
                  ox:li.oriX, oy:li.oriY, oz:li.oriZ,
                  ch:li.innerHTML,
                  theta:li.circleTheta, phi:li.circlePhi,
                  tex:makeCharTex(li.innerHTML)
                });
              }

              // 字符四边形半尺寸 = 导出字体大小的一半（和预览中字符占据的空间一致）
              var quadHalf=exportFontSize/2;

              var quadIdx=new Uint16Array([0,1,2,0,2,3]);
              var qib=gl2.createBuffer();
              gl2.bindBuffer(gl2.ELEMENT_ARRAY_BUFFER,qib);
              gl2.bufferData(gl2.ELEMENT_ARRAY_BUFFER,quadIdx,gl2.STATIC_DRAW);
              var qvb=gl2.createBuffer();
              gl2.bindBuffer(gl2.ARRAY_BUFFER,qvb);
              gl2.bufferData(gl2.ARRAY_BUFFER,9*4*4,gl2.DYNAMIC_DRAW);

              // 预览 CSS 没有设置 perspective 属性，preserve-3d 下无透视缩放
              // 等效于正交投影。用正交矩阵匹配预览效果。
              // 预览坐标系：li 定位在 (x+r, y+r, z)，然后 translate(-50%,-50%) 居中
              // box 左上角在 middle 的 (10vw, 10vw)（因为 box 80% 居中于 100vw）
              // 映射到导出 canvas：box 左上角在 (eS*0.1, eS*0.1)
              // 球心在 box 中心 = (eS*0.1 + eR, eS*0.1 + eR) = (eS/2, eS/2)
              // 正交投影：将世界坐标 [-eS/2, eS/2] 映射到 NDC [-1, 1]
              var halfS=eS/2;
              // ortho(-halfS, halfS, -halfS, halfS, -2000, 2000)
              var ortho=new Float32Array([
                1/halfS, 0, 0, 0,
                0, 1/halfS, 0, 0,  // Y 不翻转
                0, 0, -1/2000, 0,
                0, 0, 0, 1
              ]);

              function eRender(){
                gl2.clearColor(0,0,0,1);
                gl2.clear(gl2.COLOR_BUFFER_BIT|gl2.DEPTH_BUFFER_BIT);
                gl2.enable(gl2.DEPTH_TEST);
                gl2.enable(gl2.BLEND);
                gl2.blendFunc(gl2.SRC_ALPHA,gl2.ONE_MINUS_SRC_ALPHA);

                var radY=tX*Math.PI/180;

                for(var i=0;i<pts.length;i++){
                  var p=pts[i];
                  // 旋转球面坐标（和预览 applyTransform 完全一致）
                  var ox=p.ox*scaleFactor, oy=p.oy*scaleFactor, oz=p.oz*scaleFactor;
                  var nx=ox*Math.cos(radY)+oz*Math.sin(radY);
                  var nz=-ox*Math.sin(radY)+oz*Math.cos(radY);
                  var ny=oy; // 正交矩阵已经翻转了 Y 轴

                  // 透明度：和预览一致 [0.2, 1]
                  var opacity=(nz+eR)/(2*eR);
                  opacity=Math.max(0.2,Math.min(1,opacity));

                  // 字符朝向：和预览 applyTransform 中的 rotateY(newPhi) rotateX(theta-PI/2) 一致
                  var newPhi=p.phi+radY;
                  var cosP=Math.cos(newPhi),sinP=Math.sin(newPhi);
                  var thetaX=p.theta-Math.PI/2; // 保持原始角度
                  var cosT=Math.cos(thetaX),sinT=Math.sin(thetaX);

                  // 组合旋转: RY(newPhi) * RX(thetaX)
                  var m00=cosP, m01=sinP*sinT, m02=sinP*cosT;
                  var m10=0,    m11=cosT,      m12=-sinT;
                  var m20=-sinP,m21=cosP*sinT, m22=cosP*cosT;

                  var model=new Float32Array([
                    m00,m10,m20,0,
                    m01,m11,m21,0,
                    m02,m12,m22,0,
                    nx,ny,nz,1
                  ]);

                  var mvp=mulM2(ortho,model);

                  var vd=new Float32Array([
                    -quadHalf,-quadHalf,0, 1,1,1,opacity, 0,1,
                     quadHalf,-quadHalf,0, 1,1,1,opacity, 1,1,
                     quadHalf, quadHalf,0, 1,1,1,opacity, 1,0,
                    -quadHalf, quadHalf,0, 1,1,1,opacity, 0,0
                  ]);

                  gl2.bindBuffer(gl2.ARRAY_BUFFER,qvb);
                  gl2.bufferSubData(gl2.ARRAY_BUFFER,0,vd);

                  var stride=36;
                  gl2.enableVertexAttribArray(aP2);
                  gl2.vertexAttribPointer(aP2,3,gl2.FLOAT,false,stride,0);
                  gl2.enableVertexAttribArray(aC2);
                  gl2.vertexAttribPointer(aC2,4,gl2.FLOAT,false,stride,12);
                  gl2.enableVertexAttribArray(aT2);
                  gl2.vertexAttribPointer(aT2,2,gl2.FLOAT,false,stride,28);

                  gl2.uniformMatrix4fv(uMVP2,false,mvp);
                  gl2.activeTexture(gl2.TEXTURE0);
                  gl2.bindTexture(gl2.TEXTURE_2D,p.tex);
                  gl2.uniform1i(uTex2,0);
                  gl2.uniform1f(uUseTex2,1.0);

                  gl2.bindBuffer(gl2.ELEMENT_ARRAY_BUFFER,qib);
                  gl2.drawElements(gl2.TRIANGLES,6,gl2.UNSIGNED_SHORT,0);
                }
              }

              var frameIdx=0,BATCH=10;
              function processBatch(){
                try{
                var batch=[];
                var end=Math.min(frameIdx+BATCH,totalSteps);
                for(var i=frameIdx;i<end;i++){
                  angleY-=1.8;tX=angleY;
                  eRender();
                  batch.push({i:i,d:ec.toDataURL('image/jpeg',0.85)});
                }
                frameIdx=end;
                window.ReactNativeWebView.postMessage(JSON.stringify({t:'b',f:batch}));
                if(frameIdx<totalSteps){setTimeout(processBatch,0);}
                else{
                  try{gl2.getExtension('WEBGL_lose_context').loseContext();}catch(e){}
                  angleY=savedAngleY;tX=angleY;
                  applyTransform(obox);
                  window.ReactNativeWebView.postMessage(JSON.stringify({t:'d',n:totalSteps}));
                }
                }catch(e){window.ReactNativeWebView.postMessage(JSON.stringify({t:'e',m:e.message}));}
              }
              processBatch();
              }catch(e){window.ReactNativeWebView.postMessage(JSON.stringify({t:'e',m:e.message}));}
            };

            return true; // 返回一个简单的支持类型
        })();
  