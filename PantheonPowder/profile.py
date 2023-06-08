#!/usr/bin/env python

kube_description= \
"""
Pantheon deployment
"""
kube_instruction= \
"""
Not instructions yet
"""


import geni.portal as portal
import geni.rspec.pg as PG
import geni.rspec.igext as IG


pc = portal.Context()
rspec = PG.Request()


# Profile parameters.
pc.defineParameter("Hardware", "Machine Hardware",
                   portal.ParameterType.STRING,"d430",[("d430","d430"),("d710","d710"), ("d820", "d820"), ("pc3000", "pc3000")])

params = pc.bindParameters()

#
# Give the library a chance to return nice JSON-formatted exception(s) and/or
# warnings; this might sys.exit().
#
pc.verifyParameters()



tour = IG.Tour()
tour.Description(IG.Tour.TEXT,kube_description)
tour.Instructions(IG.Tour.MARKDOWN,kube_instruction)
rspec.addTour(tour)


# Machine
machine = rspec.RawPC("pantheon")
machine.disk_image = 'urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU18-64-STD'
machine.hardware_type = params.Hardware
machine.addService(PG.Execute(shell="bash", command="/local/repository/scripts/setup_pantheon.sh"))


#
# Print and go!
#
pc.printRequestRSpec(rspec)
