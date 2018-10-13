uniform float brightness; // slider[0.,1.,.05] 0.5
uniform float value; // slider[0.,1.,.05] 0.5

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;
    vec3 col = value + brightness * cos(iTime + uv.xyx + vec3(0, 2, 4));
    float d = length(uv.x - .5) * length(uv.y - .5);
    col *= smoothstep(0., .001, d);
    fragColor = vec4(col, 1.0);
}
