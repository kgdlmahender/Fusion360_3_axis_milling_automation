# For this sample script to run, the active Fusion document needs at least one CAM operation.

import adsk.core, adsk.fusion, adsk.cam, traceback

app = adsk.core.Application.get()
ui = app.userInterface

def criticalError(message:str):
    ''' Customised messageBox to handle critical errors in one line '''
    ui.messageBox(  message,
                    'Critical Error',
                    adsk.core.MessageBoxButtonTypes.OKButtonType,
                    adsk.core.MessageBoxIconTypes.CriticalIconType)

def run(context):
    try:
        doc: adsk.core.Document = app.activeDocument
        products: adsk.core.Products = doc.products
        try:
            product: adsk.core.Product = products.itemByProductType('CAMProductType')
        except Exception:
            product = None

        # Check if the document has a CAMProductType, abandon cleanly if not.
        operationErrorMsg = 'This script requires the active document to contain at least one CAM operation.'
        if product == None:
            criticalError(operationErrorMsg)
            return

        cam = adsk.cam.CAM.cast(product)

        # Initialize the CAM manager to access the library manager and the post processor library.
        camManager = adsk.cam.CAMManager.get()
        libraryManager: adsk.cam.CAMLibraryManager = camManager.libraryManager
        postLibrary: adsk.cam.PostLibrary = libraryManager.postLibrary

        # Create a query to filter post processors from the Fusion library by the vendor "Autodesk".
        postQuery: adsk.cam.PostConfigurationQuery = \
                postLibrary.createQuery(adsk.cam.LibraryLocations.Fusion360LibraryLocation)
        postQuery.vendor = "Autodesk"

        # Set the post configuration to use based on Operation Type of the first Setup.
        try:
            firstSetupOperationType: adsk.cam.OperationTypes = cam.setups.item(0).operationType
        except:
            criticalError(operationErrorMsg)
            return

        if firstSetupOperationType == adsk.cam.OperationTypes.MillingOperation:
            postQuery.capability = adsk.cam.PostCapabilities.Milling
        elif firstSetupOperationType == adsk.cam.OperationTypes.TurningOperation:
            postQuery.capability = adsk.cam.PostCapabilities.Turning
        elif firstSetupOperationType == adsk.cam.OperationTypes.JetOperation:
            postQuery.capability = adsk.cam.PostCapabilities.Jet

        postConfigs: list[adsk.cam.PostConfiguration] = postQuery.execute()

        # Check for post configs being available.
        if len(postConfigs) == 0:
            criticalError('No post-configurations found.')
            return
    
        # Find the post required in the post library and import it to local library.
        postRequired = "RS-274D"
        postDescription = None
        for config in postConfigs:
            if config.description == postRequired:
                postDescription = postRequired
                ncExtension = config.extension
                url = adsk.core.URL.create("user://")
                importedURL = postLibrary.importPostConfiguration(config, url, "NCProgramSamplePost.cps")
                break

        # Check if the required post was found, abandon cleanly if not.
        if not postDescription:
            criticalError(f'Unable to find postprocessor {postRequired}.')
            return
        
        # Get the imported local post config.
        postConfig: adsk.cam.PostConfiguration = postLibrary.postConfigurationAtURL(importedURL)

        # Prompt the user with an option to view the resulting NC file.
        dlgResults: adsk.core.DialogResults = ui.messageBox(
                                    'View results when post is complete?', 'Post-processing',
                                    adsk.core.MessageBoxButtonTypes.YesNoButtonType,
                                    adsk.core.MessageBoxIconTypes.QuestionIconType)
        viewResult: bool  = (dlgResults == adsk.core.DialogResults.DialogYes)

        # Create ncInput object.
        ncInput: adsk.cam.NCProgramInput = cam.ncPrograms.createInput()

        # Set the value of scenario to 1, 2 or 3 to post all, post the first setup,
        # or post only the first operation of the first setup.
        scenario = 1

        # Spaces appended to the title make the messageBox wider, preventing linw wrapping.
        mbChoice: adsk.core.DialogResults = ui.messageBox(
                                    "Yes \t- All toolpaths will be posted.\n\n" \
                                    "No \t- Toolpaths in the first setup will be posted.\n\n" \
                                    "Cancel\t- The first toolpath in the first setup will be posted.\n",
                                    "Select what should be post-processed                                   ",
                                    adsk.core.MessageBoxButtonTypes.YesNoCancelButtonType, 
                                    adsk.core.MessageBoxIconTypes.QuestionIconType)

        if (mbChoice == adsk.core.DialogResults.DialogYes):
            scenario = 1
        elif (mbChoice == adsk.core.DialogResults.DialogNo):
            scenario = 2
        else:
            scenario = 3

        # Adjust NC program parameters.
        ncInput.displayName = 'Sample NCProgram'

        # Embelish the nc filename to indicate chosen scenario and programming language.
        programName:str = f'NCProgramSamplePy{scenario}'
        programfilename: adsk.cam.CAMParameter = ncInput.parameters.itemByName('nc_program_filename')
        programfilename.value.value = programName

        # Provide a comment at the top of the file.
        comment: adsk.cam.CAMParameter = ncInput.parameters.itemByName('nc_program_comment')
        comment.value.value = "This is the Post Toolpaths API Sample NC Program"

        # Open nc file in editor if earlier requested.
        openInEditor: adsk.cam.CAMParameter = ncInput.parameters.itemByName('nc_program_openInEditor')
        openInEditor.value.value = viewResult

        # Set temp directory as output directory
        # Make the path valid for Fusion by replacing \\ to / in the path
        outputFolder = str(cam.temporaryFolder).replace('\\', '/') 
        ncInput.parameters.itemByName('nc_program_output_folder').value.value = outputFolder
        
        if scenario == 1:
            # ncInput.operations() expects a list of type 'OperationsBase': Operation, CAMFolder, CAMPattern, Setup
            # It will not accept CAMFolders, CAMPatterns or Setups (all plural) as they are derived from core.Base
            opsBaseList: list[adsk.cam.OperationBase] = []
            setups: adsk.cam.Setups = cam.setups
            for setup in setups:
                opsBaseList.append(setup)
            ncInput.operations = opsBaseList # Include all setups
        elif scenario == 2:
            ncInput.operations = [cam.setups.item(0)]  # Only include the first setup
        elif scenario == 3:
            firstSetup: adsk.cam.Setup = cam.setups.item(0)
            firstOperation: adsk.core.Base = firstSetup.allOperations.item(0)
            if firstOperation.hasToolpath:
                ncInput.operations = [firstOperation]  # Only include the first operation of the first setup
            else:
                ui.messageBox('Operation has no toolpath to post')
                return

        # Create a new NC program using the current NC Program input including specified parameters and operations
        newProgram: adsk.cam.NCProgram = cam.ncPrograms.add(ncInput)

        # Configure the post processor
        newProgram.postConfiguration = postConfig

        # Example of changing a post parameter. Parameters need to be declared as their correct type.
        postParams: adsk.cam.CAMParameters = newProgram.postParameters

        # Parameter builtin_tolerance is of Type FloatParameterValue.
        builtInTolerance: adsk.cam.FloatParameterValue = postParams.itemByName('builtin_tolerance')
        builtInTolerance.value.value = 0.004

        # Parameter showSequenceNumbers is of type ChoiceParameterValue so "false" is a string not a boolean.
        showSequenceNumbers: adsk.cam.ChoiceParameterValue = postParams.itemByName('showSequenceNumbers')

        # Not all posts support SequenceNumbers
        if showSequenceNumbers:
            showSequenceNumbers.value.value = str('false')
        else:
            criticalError(f'Parameter showSequenceNumbers cannot be modified for postprocessor: {postRequired} - skipping!')

        # Update to apply changes.
        newProgram.updatePostParameters(postParams)

        # Finally post the process.
        postOptions = adsk.cam.NCProgramPostProcessOptions.create()
        newProgram.postProcess(postOptions)

        # Prompt user with an option to switch to the CAM workspace if it's not already active
        if ui.activeWorkspace.name != 'Manufacture':
            activateCAMWorkspace: adsk.core.DialogResults = ui.messageBox(
                                    f'Activate the CAM Workspace?','CAM Workspace Activate',
                                    adsk.core.MessageBoxButtonTypes.YesNoButtonType,
                                    adsk.core.MessageBoxIconTypes.QuestionIconType)

            if activateCAMWorkspace == adsk.core.DialogResults.DialogYes:
                camWorkspace: adsk.core.Workspace = ui.workspaces.itemById("CAMEnvironment")
                camWorkspace.activate()

        # Indicate completion.
        ui.messageBox(f'See file:\n{outputFolder}/{programName}{ncExtension}',
                      'Post processing is complete  \t\t\t\t\t'); # Prevent line breaks of the pathname

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))