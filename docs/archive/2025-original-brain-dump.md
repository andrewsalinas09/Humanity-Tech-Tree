> **Archived 2026-08-08.** This is the original stream-of-consciousness README, preserved verbatim. Its content has been distilled into docs/ (ADRs, ARCHITECTURE, OPEN-QUESTIONS). Do not treat it as current.

The goal of this project is to create a tech tree for all of humanity from technology to culture.

The idea is that it is a knowledge graph for connections being dependencies from parent to child. 

For example a battery can have and edge to lithium. (This is incomplete for example you may want liion battery)

This brings the first point up. This graph needs to be easily editable. For example adding a parent or child. Adding a parent is easy since the children down't change. For example adding battery as a parent to liion. All the children of liion don't change. 
Adding a sub child is a little tricker. For example if we add liion as a child to battery, all of the children of battery may need to change to really be liion. To handle this we will kick all the children off and add them to a queue. 
An LLM will determine if it should go to the new child or stay as is. Then it will go to a secondary queue for humans to review. 

We need a good way to review bulk and quickly and make sure people can't vandalize the graph. 

Layer 1: The blast radius. 
The damage a user can do should be inversely proportional to the importance of the node. 
Leaf Node (iPhone 25): 0 Dependents. Low Risk.
Root Node (Physics): 1,000,000 Depends. Critical Risk.

You limit who can touch a node based on its "Dependency Weight"
New User: Can only edit nodes with < 5 dependents. (They can add new things, but they can't break "Steam Engine")
Verified User: Can edit nodes with < 100 dependents. 
Elder/admin: Can edit "Core" nodes (Roots, Abstracts)

Layer 2: The "Shadow Branch" (isolation)
New let a user write directly to the MASTER database. When a user "Adds a Node," they are actually creaating a Proposed Branch. 
1. User Action: User adds Banana -> Nuclear Bomb
2. System State:
   The World: sees the old Nuclear Bomb (Safe)
   The User: Sees their "Modded" Nuclear Bomb
3. The "Merge" Process:
   The edit sits in a PENDING queue.
    The other users (or AI) review it.
    Only after approval does it get merged into the Master Graph.

Layer 3: The "Circuit Breaker"
1. Cycle Detenction (Did the user create a loop? Iron -> Steel -> Iron) And it wasn't a part of an optimization edge. Reject immedtiely
2. Disconnect Check: Did the user delete an edge that leaves 50 children orphaned? Reject (or have users review but probably wrong)
3. Use a cheap embedding / AI model.
   User connects Banana to Nuclear Bomb
    AI Check: Distance > Threshold
    Flag for manual review

Layer 4: The "Trust Chain" (Repuation)
    a new node is in the shadow branch until 3 users "Vouch" for it (upvote)
    If a user vouches for vandalism, they lose reputation too.
    This creates an "Immunite System" Users won't blindly click "yes" because if they approve spam, their own ability to edit gets revoked.

Handling the Bot Problem (Layer 2 & 3 Integration)
Bots are the primary threat to Layer 2, as they can "vote-stuff" a proposal to make it look legitimate. To counter this, you can use Proof of Work and Behavioral Fingerprinting:
Reputation "Vesting": A user cannot vote on a proposal immediately after joining. They must have a "Vested" history of accepted leaf-node contributions before their vote carries weight in Layer 2.
The Embedding "Sentinel": Use your embedding logic (Layer 3) to flag "Anomaly Clusters." If 50 new bots all join and vote for a connection that has a massive semantic distance (e.g., Bluetooth $\rightarrow$ Medieval Siege Engines), the system triggers a "Circuit Breaker" and freezes that node for admin review.
Graph-Based Bot Detection: Use Neo4j to look for "Sybil Attacks." If a group of users only ever votes on each other's nodes and has no connection to the rest of the community, they are flagged as a botnet.

Version Control safety net
Atomic Rollbacks. Ways to reverse sections of the graph. 


There's the concept of abstract ideas, for example battery or iPhone or GoPro, and then you will have specific instances of those ideas.

iPhone will depends on for example ARM CPU and then all the children will connect to the specific Instance for example Armv7 or Armv8.

Gopro connects to GPS but then the relase of the 12 means we need a way to drop that edge for the abstract GoPro to all the children, and then we remove it from that singular child. 

Each edge will have an id, and then a from node and to node. There will be a type for example optimized or instance of. iPhone 15 is instance of iPhone. Haaber process optimizes food production.

A huge part of the graph will be these constraints that force the paths to take a specific route. We also must let true things be true and it's ok if it's not perfect. For example iPhone connects to cpu which containts to switching technology or soemthing like that which is connected to vacuum tubes. Now this is technically wrong but OK. You could in theory make an iPhone with vacuum tubes.
We then add a contraignt like size needs to be some widght. Then it will automatically prune out that path and be foreced to go the transisotr route. We will basically simulate the idea that when people design something they are trying to optimize for a specific use case. If I have powertool connect to liion battery there will be some optimize contaight on that edge that's like 1kW power, which forces the SOTA optimize path to be taken. It also makes sure that you can't crate power tools unless you have that opti8mizer path.
If a user sees that they can create an iPhone with a vacuum, tube, they can flag it as a mistake and then someone else can rewivwe it and fix it / they can also do it themselves. It makes a fun game on the home page where you can have people go and try and fix all the current flags and what not. If they add that consraint then either it'll take the new optimizatin path OR it'll then be marked as unrealized which makes another bountry on the home page. "iPhone has no path through battery" and then they can figured out the missing technlogoly that satisfies the constaint that was added.

Each edge also has epistemic status and validaty status. For example, epistemic status can be:
mainstream fact, (the earth is round) (the pyramids were built by egyptionas)
high confidence (vikings reached america)
debated (shakespare authored question)
uncertain origin (who invented the compass first)

fringe theoyr (alians built the pyramids)
mytholoogy (though idk if i want this but I will probbaly add it and let users prune certain edges)

Validity Status:
Current truth (germ theory)
disproven (phlogiston)
supeseded (newtonian physics)
hypothetical (string theory)
subjective (art / moderism, etc..)

start and end data (for that edge, multiple edges for multiple start and end dates) for example roman concrete

logic group:
    this gives a way to have multiple different satisfiers
    functional group id (for example primary material = 0, catalyst = 1)
    variant id (for catalyst 0 = platinum, 1 = palladium + heat)
    part_id (if variant is 1 then part 0 is palladium and part 2 is heat)

    this lets you have multiple things you need and for each thing multiple ways to satisfy it and for each multiple way multiple things in that way

    image if widget A needs (material 0, material 1, ((possibility 1), (possibiulity 2 + 3 + 4)))


impact weight (fairly subjective but how important is this edge)



Then each node has a:
    Category: 
        biological entity (human, alians)
        origination (the royal society)
        geopolitical entity (germany)
        work_publication (the book)
        legislation (copywrite, resource shortage)
        historical event (WWII)
        societyal era
        belief system (miasma, geocentrism)
        natural phenomenon (hurricanes, malaria, things not made by humans but influence humans)
        natural law (thermodynamics, E&M)
        formal concept (boolean logic, calculus)
        capability (prevision < 0.01mm, global instant comms (can maybe tie into optimization factors)
        material (steel, silicon, rubber)
        method technique (casting, photolithography, triangulation)
        standard unit (meter, TCP/IP, IEEE 754, IEEE 802.11)
        Technology (everything is a technology that we event other than material)
    Validity:
        same as the edge validity
    current state:
        locked (impossible (physics constraint or parents missing (can't building computer without a CPU parent)))
        THEORETICAL     Concept valid, but no Instances are working. (Vaporware)
        REALIZED         Concept valid + >0 Instances are functional.

    RegionalAvailability:
       historical region (what was it called when it was invented)
        current region (what do we call it now)
        coordinates (what are the exact coordinates)

        Timeline:
           list of time segments [active (0-400) -> list (400-1400) active (1400-present)] 
                Datapoint start:
                    year
                    uncertainty range
                    Timescale:
                        geological (2MYA)
                        archaelogical (Bronze Age)
                        historical (July 4th, 1776)
                        mythological (before time)
                optional datapoint end
                Knowledge status:
                    active (people use this daily)
                    theoretical (leonardo's tank)
                    lost (roman concrete in 600AD)
                    obsolete (we know but choose not to (steam locomotive)
                    mythical (tower of babel)
                transisiotn reason (why did it start / end)



        is indigenous (Did it start here)
        import source (where did it come from?)
            


        



A goal of this tech tree is to see how techynology boostrapped itself and grew, for example having iron make tools which make steel which make better steel. This loop needs to be optimiation in order to have an end to the cycle. (however the number of loops will be based on what technology you need for example airplane turbine blade may need to go up through many loops before it can be made)

Anoterh goal is to be able to develop things from first principles.

Some examples:
things never depend on people directly (unless they do) for exampel calculate shoudln't depeing on isaac newton, it should dependin on the works he creatged, but WWI may have a direct link to Arch Duke Frankz furdinant
Wifi connects to frequency hopping which connects to works from hedi lamar, but not her directly. 

When you insert a node and it is an "is type of" edge, then need to take all edges from the parent that go to "is component / ingrediant" and add it to the check queue for that new "is type of" node
For example you have a battery, you add a new node called "LiIon" and it is a type of battery. You need to add all the edges from battery to "is component" to the check queue to see if we need to move them LiIon.

Usually if a node is "Abstract" like battery, then you shouldn't be able to add "is componet / ingrediant" to it, you must have an actual instance of it first. For example liion is type of battery. 
I suppose we also need to do the same for "is refineement of" edges as DDR -> DDR4 may need edges from DDR to actually go to DDR4.