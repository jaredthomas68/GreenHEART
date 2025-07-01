import openmdao.api as om
from numpy import ones


class OpenLoopControllerBaseClass(om.ExplicitComponent):
    """
    Base class for open-loop controllers in the H2Integrate system.

    This class provides a template for implementing open-loop controllers. It defines the
    basic structure for inputs and outputs and requires subclasses to implement the `compute`
    method for specific control logic.

    Attributes:
        plant_config (dict): Configuration dictionary for the overall plant.
        tech_config (dict): Configuration dictionary for the specific technology being controlled.
    """

    def initialize(self):
        """
        Declare options for the component. See "Attributes" section in class doc strings for
        details.
        """

        self.options.declare("plant_config", types=dict)
        self.options.declare("tech_config", types=dict)

    def setup(self):
        """
        Define inputs and outputs for the component.

        Inputs:
            {resource_name}_in (array(float)): Input timeseries representing the resource flow into
            the storage or system. The name is dynamically determined by the `resource_name` in
            the `tech_config`.

        Outputs:
            {resource_name}_out (array(float)): Output timeseries representing the resource flow out
            of the storage or system. The name is dynamically determined by the `resource_name` in
            the `tech_config`.
        """

        resource_name = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_name"
        ]
        resource_units = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_units"
        ]

        self.add_input(
            f"{resource_name}_in",
            shape_by_conn=True,
            units=resource_units,
            desc=f"{resource_name} input timeseries from production to storage",
        )

        self.add_output(
            f"{resource_name}_out",
            copy_shape=f"{resource_name}_in",
            units=resource_units,
            desc=f"{resource_name} output timeseries from plant after storage",
        )

    def compute(self, inputs, outputs):
        """
        Perform computations for the component.

        This method must be implemented in subclasses to define the specific control logic.

        Args:
            inputs (dict): Dictionary of input values.
            outputs (dict): Dictionary of output values.

        Raises:
            NotImplementedError: If the method is not implemented in a subclass.
        """
        raise NotImplementedError("This method should be implemented in a subclass.")


class PassThroughOpenLoopController(OpenLoopControllerBaseClass):
    """
    A simple pass-through controller for open-loop systems.

    This controller directly passes the input resource flow to the output without any
    modifications. It is useful for testing, as a placeholder for more complex controllers,
    and for maintaining consistency between controlled and uncontrolled frameworks as this
    'controller' does not alter the system output in anyway.
    """

    def compute(self, inputs, outputs):
        """
        Pass through input to output flows.

        Args:
            inputs (dict): Dictionary of input values.
                - {resource_name}_in: Input resource flow.
            outputs (dict): Dictionary of output values.
                - {resource_name}_out: Output resource flow, equal to the input flow.
        """
        resource_name = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_name"
        ]

        outputs[f"{resource_name}_out"] = inputs[f"{resource_name}_in"]

    def setup_partials(self):
        """
        Declare partial derivatives as unity throughout the design space.

        This method specifies that the derivative of the output with respect to the input is
        always 1.0, consistent with the pass-through behavior.
        """

        resource_name = self.options["tech_config"]["model_inputs"]["shared_parameters"][
            "resource_name"
        ]

        # Get the size of the input/output array
        size = self._get_var_meta(f"{resource_name}_in", "size")

        # Declare partials for all elements based on the eigenvector
        self.declare_partials(
            of=f"{resource_name}_out",
            wrt=f"{resource_name}_in",
            rows=range(size),
            cols=range(size),
            val=ones(size),
        )
