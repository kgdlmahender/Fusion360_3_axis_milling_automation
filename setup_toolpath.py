import adsk.core, adsk.cam, adsk.fusion, os, traceback

# Constants
#MILLING_TOOL_LIBRARY_URL = adsk.core.URL.create('systemlibraryroot://Samples/Milling Tools (Metric).json')

MILLING_TOOL_LIBRARY_URL = adsk.core.URL.create('systemlibraryroot://Local//Library.json')
#DRILLING_TOOL_LIBRARY_URL = adsk.core.URL.create('systemlibraryroot://Samples/Hole Making Tools (Metric).json')
TEMPLATE_FILENAME = "C://Users//kgdlm//Dropbox//My PC (LAPTOP-MQBA6R0M)//Documents//projects//fusionapi//templates//12mm_tool_template.f3dhsm-template"

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        doc = app.activeDocument
        products = doc.products

        # Switch to manufacturing workspace
        camWS = ui.workspaces.itemById('CAMEnvironment')
        camWS.activate()

        # Get the CAM product
        cam = adsk.cam.CAM.cast(products.itemByProductType("CAMProductType"))
        if not cam:
            ui.messageBox("No CAM product found. Make sure a CAM product is active.")
            return

        # Get the design product
        design = adsk.fusion.Design.cast(products.itemByProductType('DesignProductType'))
        rootComponent = design.rootComponent
        body = rootComponent.bRepBodies.item(0)  # Assuming at least one body exists
        if not body:
            ui.messageBox("No body found in the design.")
            return

        # Create a setup
        setup = createSetup(cam, body)

        # Apply the template to the setup
        applyTemplateToSetup(cam)

        ui.messageBox("Setup and template applied successfully.")

    except Exception as e:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def createSetup(cam, body):
    """Creates a CAM setup."""
    setups = cam.setups
    input = setups.createInput(adsk.cam.OperationTypes.MillingOperation)
    input.models = [body]
    input.stockMode = adsk.cam.SetupStockModes.RelativeBoxStock

        # Set the origin to be at the top center of the model box.
    originParam = input.parameters.itemByName('wcs_origin_mode')
    choiceVal: adsk.cam.ChoiceParameterValue = originParam.value
    choiceVal.value = 'stockPoint'

    originPoint = input.parameters.itemByName('wcs_origin_boxPoint')
    choiceVal: adsk.cam.ChoiceParameterValue = originPoint.value
    choiceVal.value = 'top 1'

    # Create the setup
    setup = setups.add(input)
    return setup

def applyTemplateToSetup(cam):
    """Applies a template to all setups."""
    ui = adsk.core.Application.get().userInterface

    # Check if the template exists
    if not os.path.exists(TEMPLATE_FILENAME):
        ui.messageBox("The template '{}' does not exist.".format(TEMPLATE_FILENAME))
        return

    setups = cam.setups
    for setup in setups:
        templateInput = adsk.cam.CreateFromCAMTemplateInput.create()
        camTemplate = adsk.cam.CAMTemplate.createFromFile(TEMPLATE_FILENAME)
        templateInput.camTemplate = camTemplate
        results = setup.createFromCAMTemplate2(templateInput)

        # Get the operation that was created and rename it
        if results:
            operation = results[0]
            operation.name = "API added operation"

    # Generate all toolpaths, skipping any that are already valid
    cam.generateAllToolpaths(True)
