# sistema multiagente con intervención humana para apoyar la preparación de artículos científicos: diseño e implementación de un prototipo

# human-in-the-loop multi-agent system for supporting scientific article preparation: design and implementation of a prototype

Mauricio Aliendre Perez (1)*

(1) Afiliación institucional, localidad y país: completar por el autor. E-mail: completar por el autor.

*Autor de correspondencia: completar dirección de correo electrónico.*

**Resumen:** Se diseñó e implementó un prototipo de software que coordina búsqueda bibliográfica, redacción, revisión asistida por modelos de lenguaje y generación de visualizaciones. Cuatro agentes especializados operan mediante un grafo de estados con dos aprobaciones humanas y persistencia en PostgreSQL. La búsqueda integra arXiv y Semantic Scholar junto con una caché exacta que conserva resultados previos. La evaluación combinó pruebas unitarias y una ejecución integral: se conservaron 13 registros tras deduplicar resultados en vivo y en caché, se generó un borrador de 837 palabras, una puntuación automática de 8,25/10 y cinco visualizaciones; las 26 pruebas unitarias pasaron. La puntuación automática no constituye validación independiente. El prototipo demuestra viabilidad de integración, pero requiere revisión experta, verificación de citas y evaluación en el dominio de aplicación antes de sustentar publicaciones.

**Palabras clave:** agentes de inteligencia artificial, generación de artículos, revisión con intervención humana, búsqueda bibliográfica, persistencia de datos.

**Abstract:** A software prototype was designed to coordinate literature search, drafting, language-model-assisted review, and visualization generation. Four specialized agents operate through a state graph with two human approval points and PostgreSQL persistence. Search integrates arXiv and Semantic Scholar alongside an exact-query cache that retains prior results. Evaluation combined unit tests and an end-to-end run: 13 records remained after deduplicating live and cached results, an 837-word draft was produced, an automated score of 8.25/10 was assigned, and five visualizations were generated; all 26 unit tests passed. The automated score is not independent validation. The prototype demonstrates integration feasibility but requires expert review, citation verification, and domain-specific evaluation before supporting publication.

**Keywords:** artificial intelligence agents, article generation, human-in-the-loop review, literature search, data persistence.

## 1. Introducción

Preparar un artículo científico exige delimitar una pregunta, identificar fuentes pertinentes, redactar con coherencia y preparar elementos de apoyo. Los modelos de lenguaje de gran tamaño (LLM, por sus siglas en inglés) asisten en tareas lingüísticas y de planificación, pero no garantizan que las referencias existan o respalden cada afirmación; por ello, la automatización útil exige dividir responsabilidades, enlazar las salidas con fuentes consultables y conservar supervisión humana.

Los agentes basados en LLM combinan razonamiento, información del entorno y herramientas externas (Xi et al., 2023). ReAct intercala razonamiento y acciones para recopilar información y responder a observaciones del entorno (Yao et al., 2023), y AutoGen ofrece una infraestructura configurable para que varios agentes cooperen (Wu et al., 2023). Estas propuestas no eliminan la necesidad de definir límites y mecanismos de error verificables en cada aplicación. La intervención humana en el ciclo (HITL, por sus siglas en inglés) sitúa a la persona dentro de la decisión para orientar o corregir la actividad automatizada (Amershi et al., 2014); en este trabajo denota las pausas de aprobación explícita antes de redactar y antes de la salida final, que no equivalen a revisión por pares.

Este trabajo describe Scientific Articles Engine, un prototipo público en Python que coordina agentes de búsqueda, escritura, revisión y visualización mediante LangGraph, con estado persistido en PostgreSQL. El objetivo es documentar la arquitectura, las decisiones de implementación y los resultados de una validación funcional; la contribución es de ingeniería de software, no un método de investigación ni prueba de que los artículos generados sean publicables. La demostración usó como tema arquitecturas Transformer (Vaswani et al., 2017) en procesamiento del lenguaje natural. El repositorio público del proyecto (Aliendre Perez, 2026) documenta los pasos completos de instalación y ejecución del agente.

## 2. Materiales y métodos

### 2.1. Tipo de trabajo y fuente de evidencia

Se realizó un estudio de diseño e implementación de un prototipo de software, acompañado de pruebas funcionales, usando como fuente primaria el repositorio público del proyecto (Aliendre Perez, 2026) contrastado con las implementaciones de los agentes, el grafo y el estado compartido. La evaluación combinó pruebas unitarias automatizadas, que verificaron comportamientos delimitados, con una ejecución de extremo a extremo que observó interoperabilidad y continuidad del flujo. No se aplicó una rúbrica externa de exactitud factual; los valores numéricos de una ejecución deben leerse como registros operativos del prototipo, no como estimaciones de eficacia generalizables.

### 2.2. Arquitectura y estado del flujo

El proyecto emplea Python y un grafo de estados compilado con LangGraph. Un estado tipado conserva el tema, los artículos recuperados, el esquema, el borrador, la evaluación, las aprobaciones, los errores y las visualizaciones; los nodos reciben el estado y devuelven actualizaciones parciales, y el grafo enruta la ejecución según condiciones definidas, lo que permite representar ciclos y pausas explícitas en lugar de encadenar llamadas independientes sin contexto persistente (LangChain, s. f.). La fábrica `AgentFactory` construye servicios compartidos y los inyecta en los agentes según protocolos de búsqueda, generación y visualización, lo que facilita sustituir o simular implementaciones en pruebas.

**Figura 1.** Flujo de datos, control y aprobación humana en Scientific Articles Engine.

```drawio
<mxfile>
  <diagram id="q6oi-feNg1-pcJABsz5L" name="Page-1">
    <mxGraphModel dx="2940" dy="2250" grid="1" gridSize="10" guides="1" tooltips="0" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <UserObject label="" mermaidData="{&#xa;  &quot;data&quot;: &quot;flowchart LR\r\n    A[Tema de investigación] --&gt; B[Buscador: arXiv + Semantic Scholar + caché]\r\n    B --&gt; C[Aprobación humana 1]\r\n    C --&gt; D[Escritor]\r\n    D --&gt; E[Revisor]\r\n    E --&gt;|Requiere revisión| D\r\n    E --&gt;|Aprobado| F[Aprobación humana 2]\r\n    F --&gt; G[Visualizador]\r\n    G --&gt; H[Artículo Markdown + visualizaciones]\r\n    B -.persiste.-&gt; I[(PostgreSQL: puntos de control y caché)]\r\n    F -.persiste.-&gt; I&quot;,&#xa;  &quot;config&quot;: null&#xa;}" id="21">
          <mxCell connectable="0" parent="1" style="group;transparentBounds=1;editIcon=1;lockedGroup=0;groupPadding=10;" vertex="1">
            <mxGeometry as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Tema de investigación" mermaidId="n:A" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Tema de investigación" id="2">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="218" x="10" y="88" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Buscador: arXiv + Semantic Scholar + caché" mermaidId="n:B" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Buscador: arXiv + Semantic Scholar + caché" id="3">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="371" x="278" y="88" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Aprobación humana 1" mermaidId="n:C" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Aprobación humana 1" id="4">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="215" x="699" y="57" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Escritor" mermaidId="n:D" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Escritor" id="5">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="115" x="964" y="57" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Revisor" mermaidId="n:E" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Revisor" id="6">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="111" x="1253" y="57" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Aprobación humana 2" mermaidId="n:F" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Aprobación humana 2" id="7">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="215" x="1482" y="57" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Visualizador" mermaidId="n:G" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Visualizador" id="8">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="146" x="1875" y="33" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="Artículo Markdown + visualizaciones" mermaidId="n:H" mermaidBaseStyle="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="Artículo Markdown + visualizaciones" id="9">
          <mxCell parent="21" style="html=1;whiteSpace=wrap;strokeWidth=1;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="54" width="318" x="2143" y="33" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="PostgreSQL: puntos de control y caché" mermaidId="n:I" mermaidBaseStyle="html=1;shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;strokeWidth=1;whiteSpace=wrap;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" mermaidBaseValue="PostgreSQL: puntos de control y caché" id="10">
          <mxCell parent="21" style="html=1;shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=10;strokeWidth=1;whiteSpace=wrap;fillColor=light-dark(#ECECFF,#1f2020);strokeColor=light-dark(#9370DB,#cccccc);fontColor=light-dark(#333333,#cccccc);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontSize=16;" vertex="1">
            <mxGeometry height="67" width="290" x="1803" y="137" as="geometry" />
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:A-&gt;B#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" mermaidBaseValue="" id="11">
          <mxCell edge="1" parent="21" source="2" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" target="3">
            <mxGeometry relative="1" as="geometry">
              <Array as="points" />
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:B-&gt;C#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=0.99;exitY=0;entryX=0;entryY=0.5;" mermaidBaseValue="" id="12">
          <mxCell edge="1" parent="21" source="3" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=0.99;exitY=0;entryX=0;entryY=0.5;" target="4">
            <mxGeometry relative="1" as="geometry">
              <Array as="points">
                <mxPoint x="674" y="84" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:C-&gt;D#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" mermaidBaseValue="" id="13">
          <mxCell edge="1" parent="21" source="4" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" target="5">
            <mxGeometry relative="1" as="geometry">
              <Array as="points" />
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:D-&gt;E#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.6111111111111112;entryX=0;entryY=0.6111111111111112;curved=1;exitX=1;exitY=0.61;entryX=0;entryY=0.61;" mermaidBaseValue="" id="14">
          <mxCell edge="1" parent="21" source="5" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.61;entryX=0;entryY=0.61;" target="6">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="1166" y="96" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="Requiere revisión" mermaidId="e:E-&gt;D#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.2592592592592593;entryX=1;entryY=0.2592592592592593;curved=1;exitX=0;exitY=0.26;entryX=1;entryY=0.26;" mermaidBaseValue="Requiere revisión" id="15">
          <mxCell edge="1" parent="21" source="6" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0;exitY=0.26;entryX=1;entryY=0.26;" target="5">
            <mxGeometry relative="1" as="geometry">
              <mxPoint as="offset" />
              <Array as="points">
                <mxPoint x="1166" y="10" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="Aprobado" mermaidId="e:E-&gt;F#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" mermaidBaseValue="Aprobado" id="16">
          <mxCell edge="1" parent="21" source="6" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" target="7">
            <mxGeometry relative="1" as="geometry">
              <Array as="points" />
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:F-&gt;G#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.2;entryX=0;entryY=0.5;" mermaidBaseValue="" id="17">
          <mxCell edge="1" parent="21" source="7" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.2;entryX=0;entryY=0.5;" target="8">
            <mxGeometry relative="1" as="geometry">
              <Array as="points">
                <mxPoint x="1750" y="60" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="" mermaidId="e:G-&gt;H#0" mermaidBaseStyle="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" mermaidBaseValue="" id="18">
          <mxCell edge="1" parent="21" source="8" style="curved=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);exitX=1;exitY=0.5;entryX=0;entryY=0.5;" target="9">
            <mxGeometry relative="1" as="geometry">
              <Array as="points" />
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="persiste" mermaidId="e:B-&gt;I#0" mermaidBaseStyle="curved=1;dashed=1;dashPattern=2 3;fixDash=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0.72;exitY=1;entryX=0;entryY=0.66;" mermaidBaseValue="persiste" id="19">
          <mxCell edge="1" parent="21" source="3" style="curved=1;dashed=1;dashPattern=2 3;fixDash=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0.72;exitY=1;entryX=0;entryY=0.66;" target="10">
            <mxGeometry relative="1" as="geometry">
              <Array as="points">
                <mxPoint x="674" y="185" />
                <mxPoint x="807" y="185" />
                <mxPoint x="939" y="185" />
                <mxPoint x="1022" y="185" />
                <mxPoint x="1166" y="185" />
                <mxPoint x="1309" y="185" />
                <mxPoint x="1423" y="185" />
                <mxPoint x="1590" y="185" />
                <mxPoint x="1750" y="185" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
        <UserObject label="persiste" mermaidId="e:F-&gt;I#0" mermaidBaseStyle="curved=1;dashed=1;dashPattern=2 3;fixDash=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0.87;exitY=1;entryX=0;entryY=0.16;" mermaidBaseValue="persiste" id="20">
          <mxCell edge="1" parent="21" source="7" style="curved=1;dashed=1;dashPattern=2 3;fixDash=1;startArrow=none;endArrow=block;endSize=7;strokeColor=light-dark(#333333,#cccccc);html=1;fontSize=16;labelBackgroundColor=light-dark(#E8E8E88D,#2a2a2a8D);fontFamily=Trebuchet MS,Verdana,Arial,sans-serif;fontColor=light-dark(#333333,#cccccc);exitX=0.87;exitY=1;entryX=0;entryY=0.16;" target="10">
            <mxGeometry relative="1" as="geometry">
              <Array as="points">
                <mxPoint x="1750" y="140" />
              </Array>
            </mxGeometry>
          </mxCell>
        </UserObject>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

*Fuente: elaboración propia a partir de la implementación del repositorio (Aliendre Perez, 2026). Diagrama en formato Mermaid, editable con draw.io.*

El flujo inicia con el tema ingresado por la persona usuaria. El buscador consulta arXiv y Semantic Scholar, combina resultados con los recuperados de la caché, elimina duplicados por título normalizado y solicita al LLM un esquema; el grafo se interrumpe antes de redactar para revisar fuentes y esquema. Tras la aprobación, el escritor produce un artículo estructurado y el revisor evalúa cuatro dimensiones, devolviendo puntuaciones y sugerencias que pueden solicitar una nueva versión. Si el borrador supera el umbral, un segundo punto de interrupción permite revisar el artículo antes de generar visualizaciones y guardar el archivo Markdown.

Reanudar en los puntos de aprobación exige preservar el cursor del grafo: la implementación actualiza el campo de aprobación en el estado persistido, consulta el punto de control más reciente y reanuda con entrada nula, evitando reiniciar nodos ya ejecutados. Una prueba de regresión con dos interrupciones confirma que la escritura ocurre una sola vez y que la visualización solo se ejecuta tras la segunda aprobación.

### 2.3. Búsqueda y caché de respaldo

arXiv y Semantic Scholar están implementados como fuentes de búsqueda independientes y concurrentes, consultadas mediante sus interfaces públicas (arXiv, s. f.; Semantic Scholar, s. f.). Si una fuente no retorna resultados, el buscador recupera registros guardados para la misma consulta desde una caché persistente antes de continuar; si ninguna fuente ni la caché aportan documentos, el flujo informa un error explícito y no solicita al LLM redactar sin fuentes.

La caché se implementó como una tabla PostgreSQL con clave derivada mediante SHA-256 sobre la consulta normalizada (minúsculas, espacios reducidos), datos bibliográficos en formato JSONB y fecha de recuperación; las entradas vigentes se conservan 30 días y los errores de lectura o escritura se tratan como avisos no fatales. La normalización no calcula similitud semántica, por lo que consultas parafraseadas no son equivalentes. La conversión de resultados de Semantic Scholar admite tanto objetos del SDK como diccionarios, y trata una URL vacía de PDF como dato opcional ausente; el servicio acepta opcionalmente una clave mediante la variable `SEMANTIC_SCHOLAR_API_KEY`, que no se almacena en el código.

### 2.4. Redacción, revisión y visualización

El escritor crea un borrador cuando no existe artículo previo o lo revisa cuando hay comentarios de evaluación, convirtiendo el texto a modelos estructurados con referencias derivadas de los documentos recuperados. El revisor asigna puntuaciones de 1 a 10 en rigor científico, calidad de citas, coherencia y calidad de redacción; el promedio determina si se alcanza el umbral configurado (7,0/10 por defecto). El enrutador aplica un límite de tres revisiones mediante un nodo dedicado que incrementa `revision_count` en la arista entre revisor y escritor antes de cada reintento; si el umbral no se alcanza tras el tercer intento, el flujo termina sin pasar a la aprobación final. La evaluación del revisor es una salida automatizada que requiere verificación humana.

El visualizador identifica oportunidades para tablas o diagramas y genera hasta cinco elementos: tablas en Markdown y diagramas o flujogramas en Mermaid, añadidos al final del documento. No se evaluó la validez semántica de los diagramas mediante un renderizador ni su legibilidad con lectores.

### 2.5. Persistencia y serialización

La interfaz de línea de comandos (CLI) utiliza el punto de control asíncrono de PostgreSQL, con `JsonPlusSerializer` configurado para admitir explícitamente las clases de modelos del flujo y respaldo de serialización pickle para los tipos que lo requieren; este respaldo exige tratar la base de datos como una fuente confiable, sin cargar registros manipulados por terceros. Una prueba verifica el viaje de ida y vuelta de los modelos y la ausencia de avisos por clases no registradas.

### 2.6. Procedimiento de evaluación

La suite unitaria se ejecutó con pytest en Python 3.14.7 (Python Software Foundation, s. f.), cubriendo agentes, servicios, serialización y reanudación de interrupciones. La ejecución integral utilizó PostgreSQL de Docker, arXiv, Semantic Scholar y un proveedor LLM de OpenAI ya configurado localmente, con un identificador de hilo nuevo y aprobación automática de los dos puntos HITL para comprobar el recorrido completo. El registro operativo y el archivo resultante evidencian que el flujo alcanzó la salida, no la calidad científica del contenido.

### 2.7. Pasos para ejecutar el prototipo

Con el entorno virtual activado y PostgreSQL disponible (por ejemplo, mediante `docker-compose up -d`), el prototipo se invoca desde la línea de comandos:

```powershell
scientific-articles-engine generate "arquitecturas Transformer en procesamiento del lenguaje natural"
```

Resultado esperado: el proceso imprime el progreso de cada agente (búsqueda, esquema, redacción, revisión), se detiene dos veces solicitando aprobación humana (fuentes/esquema y artículo final) y, tras confirmar ambas, guarda el artículo generado como archivo Markdown en el directorio `output/` junto con sus visualizaciones.

## 3. Resultados y discusión

### 3.1. Componentes implementados

La Tabla 1 sintetiza los componentes observados en el código y su producto inmediato. Las responsabilidades son distintas, pero el valor del prototipo depende de la coordinación del estado compartido y de los servicios externos.

**Tabla 1.** Componentes funcionales y resultados de cada etapa.

| Componente | Entrada principal | Operación | Salida o control |
| :--- | :--- | :--- | :--- |
| Buscador | Tema y límites de consulta | Consultas concurrentes, deduplicación, caché y esquema | Registros bibliográficos y esquema |
| Aprobación 1 | Registros y esquema | Pausa para decisión de la persona usuaria | Aprobación, rechazo o nueva búsqueda |
| Escritor | Esquema, tema y referencias | Generación o revisión del borrador | Artículo estructurado |
| Revisor | Artículo y umbral | Evaluación en cuatro criterios | Puntuaciones, sugerencias y enrutamiento |
| Aprobación 2 | Artículo aprobado por revisor | Pausa previa a visualización | Aprobación final o terminación |
| Visualizador | Artículo y tema | Identificación y creación de tablas/diagramas | Lista de elementos para el Markdown |
| Persistencia | Estado del grafo y documentos | PostgreSQL, puntos de control y tabla JSONB de caché | Reanudación y recuperación exacta |

*Fuente: elaboración propia a partir del código del proyecto (Aliendre Perez, 2026).*

### 3.2. Validación funcional observada

La versión documentada incorpora 26 pruebas unitarias; las 26 finalizaron satisfactoriamente, con cuatro advertencias de Pydantic por configuración de modelos con la clase `Config` heredada. Las pruebas cubren, entre otros comportamientos, continuidad ante ausencia de resultados de una fuente, recuperación desde caché, manejo de ausencia de artículo, serialización de modelos, conversión de objetos de Semantic Scholar y reanudación después de dos aprobaciones.

En la ejecución final, el buscador combinó diez resultados de arXiv con registros recuperados de la caché de coincidencia exacta, conservando trece documentos únicos tras la deduplicación. El esquema se generó y fue aprobado automáticamente para la prueba; el escritor produjo un borrador de 837 palabras y el revisor automatizado emitió 8,25/10, por encima del umbral de configuración de 7,0. Tras la segunda aprobación, el visualizador generó cinco elementos y la interfaz de línea de comandos (CLI) guardó el resultado en Markdown.

**Tabla 2.** Indicadores observados en la ejecución de demostración.

| Indicador | Valor observado | Interpretación |
| :--- | :--- | :--- |
| Documentos de arXiv | 10 | Resultado de una consulta real con máximo configurado de 10 |
| Registros cargados de caché | 13 | Coincidencia exacta normalizada para el mismo tema; vigente según la política local |
| Registros únicos en estado | 13 | Resultado después de la deduplicación del flujo ejecutado |
| Extensión del borrador | 837 palabras | Recuento del artículo producido en esa ejecución, no un promedio |
| Puntuación automática | 8,25/10 | Promedio devuelto por el agente revisor; no calificación de expertos |
| Visualizaciones | 5 | Máximo observado en una ejecución completa |
| Pruebas unitarias | 26 de 26 aprobadas | Resultado de la suite unitaria actual |

*Fuente: registro local de ejecución y suite del repositorio; elaboración propia. Las cifras corresponden a una sola ejecución demostrativa.*

### 3.3. Incidentes de integración y correcciones

Cinco ajustes resultaron determinantes: usar `stream_mode="values"` para que el CLI reciba el estado completo del grafo en lugar de actualizaciones por nodo; detener el flujo con el mensaje del nodo antes de acceder a propiedades de un artículo nulo; habilitar la serialización explícita de los modelos Pydantic para persistir la pausa de aprobación; actualizar el estado del hilo en el punto de control y recuperar la configuración más reciente antes de reanudar cada aprobación HITL; y tolerar en la conversión de Semantic Scholar tanto objetos del SDK como diccionarios y campos opcionales vacíos. Estos incidentes muestran que la integración de agentes depende de la persistencia, la semántica del flujo y la validación de modelos, no solo de las instrucciones al modelo de lenguaje; los remedios son específicos de este prototipo.

### 3.4. Alcance y significado de la caché

La estrategia de búsquedas independientes con respaldo en caché permite continuar el flujo aun cuando alguna fuente bibliográfica no aporte resultados en un momento dado. La caché no garantiza similitud semántica: solo reutiliza consultas iguales tras normalizar mayúsculas y espacios, y descarta entradas con más de 30 días; los registros pueden quedar desactualizados y una misma pregunta puede tener formulaciones pertinentes que no coincidan exactamente. Para publicaciones que requieran actualidad convendría registrar procedencia por documento, fecha de publicación y política de expiración; una extensión con búsqueda semántica exigiría evaluar umbrales, embeddings y costos adicionales.

### 3.5. Alcance de los resultados y límites



## 4. Conclusiones

Se diseñó y documentó un prototipo de preparación asistida de artículos científicos organizado en cuatro agentes especializados y un grafo con estado persistente. La combinación de búsquedas independientes, deduplicación, caché exacta, serialización de modelos y reanudación explícita ante dos aprobaciones permitió completar una demostración integral, en la que se mantuvieron trece documentos tras deduplicación, se generó un borrador de 837 palabras, el revisor asignó 8,25/10, se produjeron cinco visualizaciones y las 26 pruebas unitarias aprobaron. Estas cifras documentan funcionalidad del sistema bajo una configuración particular y no constituyen evidencia de exactitud científica ni de generalización a otras disciplinas.

Las contribuciones principales son de ingeniería: separación de responsabilidades por agente, contratos de servicio, recuperación ante ausencia de resultados de una fuente, persistencia de resultados de consulta, protección frente a errores de serialización y pruebas de regresión para el ciclo HITL; el desarrollo mostró además que los puntos de integración —formas de salida de SDK, enlaces opcionales, cursor de checkpoint— requieren pruebas además de instrucciones a los modelos.

Como trabajo futuro se recomienda evaluar el sistema con un corpus validado por especialistas, medir precisión, cobertura, actualidad y proporción de citas respaldadas, e incorporar procedencia documental detallada. El repositorio público del proyecto (Aliendre Perez, 2026) contiene la documentación necesaria para instalar el entorno y ejecutar el agente completo.

## Agradecimientos

Este trabajo no recibió financiación externa ni institucional; fue desarrollado de forma independiente por el autor. Se comparte como una muestra abierta del trabajo que actualmente realiza en el área de agentes de inteligencia artificial, con la intención de documentar decisiones de diseño reales y, sobre todo, de servir como material introductorio que motive a estudiantes interesados a profundizar en el diseño e implementación de sistemas multiagente.

## Referencias

Aliendre Perez, M. (2026). *Scientific Articles Engine* [software]. GitHub. Recuperado de https://github.com/MauricioAliendre182/ScientificArticlesAgents

Amershi, S., Cakmak, M., Knox, W. B., & Kulesza, T. (2014). Power to the people: The role of humans in interactive machine learning. *AI Magazine*, 35(4), 105–120. https://doi.org/10.1609/aimag.v35i4.2513

arXiv. (s. f.). *arXiv API user manual*. Recuperado el 26 de septiembre de 2026 de https://info.arxiv.org/help/api/user-manual.html

LangChain. (s. f.). *LangGraph documentation: Overview*. Recuperado el 26 de septiembre de 2026 de https://docs.langchain.com/oss/python/langgraph/overview

Python Software Foundation. (s. f.). *Python 3.14 documentation: asyncio runners*. Recuperado el 26 de septiembre de 2026 de https://docs.python.org/3/library/asyncio-runner.html

Semantic Scholar. (s. f.). *Academic Graph API documentation*. Recuperado el 26 de septiembre de 2026 de https://api.semanticscholar.org/api-docs/graph

Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., & Polosukhin, I. (2017). Attention is all you need. En *Advances in Neural Information Processing Systems 30* (pp. 5998–6008). Curran Associates. Recuperado de https://papers.neurips.cc/paper_files/paper/2017/hash/3f5ee243547dee91fbd053c1c4a845aa-Abstract.html

Wu, Q., Bansal, G., Zhang, J., Wu, Y., Li, B., Zhu, E., Jiang, L., Zhang, X., Zhang, S., Liu, J., Awadallah, A. H., White, R. W., Burger, D., & Wang, C. (2023). *AutoGen: Enabling next-gen LLM applications via multi-agent conversation* (arXiv:2308.08155). https://doi.org/10.48550/arXiv.2308.08155

Xi, Z., Chen, W., Guo, X., He, W., Ding, Y., Hong, B., Zhang, M., Wang, J., Jin, S., Zhou, E., Zheng, R., Fan, X., Wang, X., Xiong, L., Zhou, Y., Wang, W., Jiang, C., Zou, Y., Liu, X., Yin, Z., Dou, S., Weng, R., Cheng, W., Zhang, Q., Qin, W., Zheng, Y., Qiu, X., & Huang, X. (2023). The rise and potential of large language model based agents: A survey (arXiv:2309.07864). https://doi.org/10.48550/arXiv.2309.07864

Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2023). ReAct: Synergizing reasoning and acting in language models. En *International Conference on Learning Representations (ICLR 2023)*. https://doi.org/10.48550/arXiv.2210.03629
