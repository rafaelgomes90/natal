import sys; sys.argv=['x']
exec(open('gera.py').read().split("CONTEM = {")[0])
W,H=1200,630
base=fio(fundo(W,H)); d=ImageDraw.Draw(base)
d.text((60,110),"NATAL DO RAFA",font=it_(26,"Bold"),fill=GOLD)
y=texto(d,(60,150),"Sua decoração de Natal",fr(52,600),CREAM,600)
y=texto(d,(60,y),"completa, no seu orçamento.",fr(52,500,True),GOLD2,600)
d.text((60,y+24),"Árvore, luzes, bolas, ponteira e saia",font=it_(28,"Medium"),fill=(201,214,204))
d.text((60,y+62),"de R$ 200 a R$ 1.200 · Mercado Livre",font=it_(28,"Medium"),fill=(201,214,204))
codes=["654010-MLA120493941857_102026","739448-MLB112438227504_062026","862174-MLB86287188296_062025","998248-MLA120309570453_102026"]
s=230
for i,c in enumerate(codes):
    ph=cobre(img(c),s,s); base.paste(ph,(690+(i%2)*(s+16),110+(i//2)*(s+16)),arred(ph,22))
base.save('/home/claude/natal/og.jpg',quality=88)
