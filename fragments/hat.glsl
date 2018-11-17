/* Fedora Shader

   Code is mainly based on
   https://www.shadertoy.com/view/4lK3Rc
   Uploaded by iq in 2017-02-24
*/

// Primitives
float smin(float a, float b, float k) {
  float h = clamp(0.5 + 0.5 * (b - a) / k, 0.0, 1.0);
  return mix(b, a, h) - k * h * (1.0 - h);
}

float sdEllipsoid(vec3 p, vec3 r) {
  float k0 = length(p / r);
  float k1 = length(p / (r * r));
  return k0 * (k0 - 1.0) / k1 + sin(p.x) * .1;
}

float sdCappedCone(vec3 p, float h, float r1, float r2) {
  vec2 q = vec2(length(p.xz), p.y);
  vec2 k1 = vec2(r2, h);
  vec2 k2 = vec2(r2 - r1, 2.0 * h);
  vec2 ca = vec2(q.x-min(q.x,(q.y < 0.0)?r1:r2), abs(q.y)-h);
  vec2 cb = q - k1 + k2*clamp( dot(k1-q,k2)/dot(k2, k2), 0.0, 1.0 );
  float s = (cb.x < 0.0 && ca.y < 0.0) ? -1.0 : 1.0;
  return s * sqrt(min(dot(ca, ca), dot(cb, cb)));
}

float sdPrismY(vec3 p, float rad, float h, float d) {
  vec3 q = abs(p);
  return max(q.y - d, max(q.x * rad + p.z * 0.5, -p.z) - h * 0.5 );
}

vec3 rotX(vec3 v, float r) {
  return vec3(v.x, cos(r) * v.y + sin(r) * v.z, -sin(r) * v.y + cos(r) * v.z);
}

float sdBox(vec3 p, vec3 b) {
  vec3 d = abs(p) - b;
  return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float sdHatTop(vec3 q) {
  float cap = sdCappedCone(q - vec3(0., 15., 0.), 3., 9., 7.) - 5.;
  float hole = length(q - vec3(0., 28.5, 0.)) - 8.;
  float plane = sdBox(q - vec3(0., 23.5, 0.), vec3(10., 1., 10.));
  float cut = sdBox(q - vec3(0., 8., 0.), vec3(20., 2.8, 20.));
  return max(-cut, max(-smin(hole, plane, 1.), cap));
}

float sdHatShape(vec3 q) {
  float top = sdHatTop(q);
  float bottom = sdEllipsoid(q - vec3(.0, 10., 0.), vec3(22., 1., 22.));
  float hole = length(q - vec3(0., 9., 0.)) - 11.;
  float shape = max(-hole, smin(bottom, top, 1.5));
  float knot = sdPrismY(rotX(q - vec3(0., 12.4, -14.), .3), 0.2, 1., 1.5);
  return knot < shape ? knot : shape;
}

float sdBand(vec3 q) {
  float band = sdBox(q - vec3(-9., 12.6, .0), vec3(25., 1.5, 25.));
  return max(band, sdHatShape(q));
}

vec2 map(vec3 q) {
  q *= 100.0;
  float hat = sdHatShape(q);
  float band = sdBand(q);
  vec2 res = band <= hat ? vec2(band, .01) : vec2(hat, 1.);
  res.x /= 100.0;
  return res;
}

vec2 intersect(vec3 ro, vec3 rd) {
  float m, t = 0.02;
  for(int i=0; i < 128; i++) {
    vec2 res = map(ro + rd * t);
    if ((res.x < 0.) || (t > 2.))
      break;
    t += res.x;
    m = res.y;
  }
  if (t > 2.)
    m = .0;
  return vec2(t, m);
}

vec3 calcNormal(vec3 pos) {
  vec3 eps = vec3(0.005, 0.0, 0.0);
  return normalize(vec3(
         map(pos+eps.xyy).x - map(pos-eps.xyy).x,
         map(pos+eps.yxy).x - map(pos-eps.yxy).x,
         map(pos+eps.yyx).x - map(pos-eps.yyx).x));
}

mat3 camRotation() {
  vec2 mo = iMouse.xy / iResolution.xy;
  float y = 1. - iTime * 0.1 + 4. * mo.x;
  float p = .6 + -6. * mo.y;
  return mat3(1., 0., 0., 0., cos(p), -sin(p), 0., sin(p), cos(p)) *
         mat3(cos(y), 0., sin(y), 0., 1., 0., -sin(y), 0., cos(y));
}

vec3 render(vec2 p) {
  mat3 rot = camRotation();
  vec3 rd = normalize(vec3(p, 1.)) * rot;
  vec3 ro = vec3(0., 0.1, -.42) * rot;
  vec3 col = vec3(.0);
  vec2 res = intersect(ro,rd);
  float t = res.x;

  if (res.y <= 0.0) {
    return col;
  }
  vec3  pos = ro + t * rd;
  vec3  nor = calcNormal(pos);
  vec3  ref = reflect(rd, nor);
  float fre = clamp(1. + dot(nor, rd), 0., 1.);
  vec3  lin = 4. * vec3(.7, .80, 1.) * (.5 + .5 * nor.y) + .5 * fre;

  col = (vec3(.9, .0, .0) * 0.72 + 0.2 * fre * vec3(1., .8, .2)) * res.y * lin;
  return col + 4. * vec3(.7, .8, 1.) * smoothstep(.0, .4, ref.y) * .4 *
         (.06 + .94 * pow(fre, 5.));
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  vec2 uv = (-iResolution.xy + 2.0 * fragCoord) / iResolution.y;
  fragColor = vec4(render(uv), 1.);
}
