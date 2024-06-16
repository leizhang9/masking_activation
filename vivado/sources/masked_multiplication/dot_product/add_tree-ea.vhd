---------------------------------------------------------------------------------------
-- Matthias Glaser (TUM)
---------------------------------------------------------------------------------------
-- Inspired by the add_tree code from the course
-- EEL4720/5721 - Reconfigurable Computing (Fall 2021) 
-- Class Project - 1D Time-Domain Convolution at the University of Florida
-- by Greg Stitt
--
-- Publicly available at:
-- http://www.gstitt.ece.ufl.edu/courses/fall21/eel4720_5721/index.html
---------------------------------------------------------------------------------------

-- The latency of the pipelined adder tree is ceil(log2(num_inputs_g))

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

use work.add_tree_pkg.all;
use work.prim_ops_pkg.all;

---------------------------------------------------------------------------------------
-- Generic Descriptions
-- num_inputs_g : The number of inputs in the adder tree
-- data_width_g : The width of each input
-- pipelined_g  : Adder tree pipelined or not
---------------------------------------------------------------------------------------

---------------------------------------------------------------------------------------
-- Port Descriptions
-- clk_i: clock
-- rst_i: reset
-- en_i : enable ('0' stalls the pipeline)
-- input_i : The inputs to the adder tree
-- output_o : The sum of all inputs 
-------------------------------------------------------------------------------

entity add_tree is
	generic (
		num_inputs_g   : positive;
		data_width_g   : positive;
		pipelined_g    : boolean := false
	);
	port (
		clk_i    : in  std_ulogic;
		rst_i    : in  std_ulogic;
		en_i     : in  std_ulogic;
		input_i  : in  std_ulogic_vector(num_inputs_g*data_width_g-1 downto 0);
		output_o : out std_ulogic_vector(data_width_g-1 downto 0));
end add_tree;

architecture rtl of add_tree is 

	function get_right_depth_f (num_inputs : natural) return natural is
		variable val : natural;
	begin
		if (num_inputs = 0) then
			val := 0;
		else
			val := integer(ceil(log2(real(num_inputs))));
		end if;

		return val;
	end get_right_depth_f;


	constant left_inputs_c  : natural := num_inputs_g - num_inputs_g/2;
	constant right_inputs_c : natural := num_inputs_g/2;
	constant left_depth_c   : natural := integer(ceil(log2(real(left_inputs_c))));
	constant right_depth_c  : natural := get_right_depth_f(right_inputs_c);
	constant depth_diff_c   : natural := left_depth_c-right_depth_c;


	signal mod_adder_intermediate_out_s : std_ulogic_vector(data_width_g-1 downto 0);
	signal mod_adder_subtrees_out_s     : std_ulogic_vector(data_width_g-1 downto 0);
	signal left_tree_out_s              : std_ulogic_vector(data_width_g-1 downto 0);
	signal right_tree_out_s             : std_ulogic_vector(data_width_g-1 downto 0);
	signal right_tree_out_unaligned_s   : std_ulogic_vector(data_width_g-1 downto 0);
	signal input_s                      : std_ulogic_vector(num_inputs_g*data_width_g-1 downto 0);
	signal output_s                     : std_ulogic_vector(data_width_g-1 downto 0);

	signal delay_reg                    : std_ulogic_vector(depth_diff_c * data_width_g-1 downto 0);

begin

	input_s  <= input_i;
	output_o <= output_s;

	one_input_gen : if (num_inputs_g = 1) generate
		output_s <= input_s;
	end generate one_input_gen;

	two_input_gen : if (num_inputs_g = 2) generate

		-- mod_add_intermediate : mod_adder 
		-- generic map (
		-- 	L_g => data_width_g
		-- )
		-- port map (
		-- 	a_i => input_s(data_width_g-1 downto 0),
		-- 	b_i => input_s(2*data_width_g-1 downto data_width_g),
		-- 	s_o => mod_adder_intermediate_out_s
		-- );

		mod_adder_intermediate_out_s <= 
			PADD(input_s(data_width_g-1 downto 0), input_s(2*data_width_g-1 downto data_width_g));

		pipelined_gen : if pipelined_g = true generate
			process(clk_i)
			begin
				if (rising_edge(clk_i)) then
					if (rst_i = '1') then
						output_s <= (others => '0');
					elsif (en_i = '1') then
						output_s <= mod_adder_intermediate_out_s;
					end if;
				end if;
			end process;
		end generate pipelined_gen;
		
		not_pipelined_gen : if pipelined_g = false generate
			output_s <= mod_adder_intermediate_out_s;
		end generate not_pipelined_gen;
		
	end generate two_input_gen;

	greater_two_input_gen : if (num_inputs_g > 2) generate

		-- mod_add_subtrees : mod_adder 
		-- generic map (
		-- 	L_g => data_width_g
		-- )
		-- port map (
		-- 	a_i => left_tree_out_s,
		-- 	b_i => right_tree_out_s,
		-- 	s_o => mod_adder_subtrees_out_s
		-- );

		mod_adder_subtrees_out_s <= PADD(left_tree_out_s, right_tree_out_s);
		
		odd_input_number_gen : if num_inputs_g mod 2 /= 0 generate

			left_tree : entity work.add_tree(rtl)
			generic map (
				pipelined_g  => pipelined_g,
				num_inputs_g => natural(num_inputs_g/2 + 1),
				data_width_g => data_width_g)
			port map (
				clk_i    => clk_i,
				rst_i    => rst_i,
				en_i     => en_i,
				input_i  => input_s(num_inputs_g * data_width_g - 1 downto data_width_g * natural(num_inputs_g/2)),
				output_o => left_tree_out_s);

			right_tree : entity work.add_tree(rtl)
			generic map (
				pipelined_g  => pipelined_g,
				num_inputs_g => natural(num_inputs_g/2),
				data_width_g => data_width_g)
			port map (
				clk_i    => clk_i,
				rst_i    => rst_i,
				en_i     => en_i,
				input_i  => input_s(data_width_g * natural(num_inputs_g/2) - 1 downto 0),
				output_o => right_tree_out_unaligned_s);

		end generate odd_input_number_gen;

		even_input_number_gen : if num_inputs_g mod 2 = 0 generate

			left_tree : entity work.add_tree(rtl)
			generic map (
				pipelined_g  => pipelined_g,
				num_inputs_g => natural(num_inputs_g/2),
				data_width_g => data_width_g)
			port map (
				clk_i    => clk_i,
				rst_i    => rst_i,
				en_i     => en_i,
				input_i  => input_s(num_inputs_g * data_width_g - 1 downto data_width_g * natural(num_inputs_g/2)),
				output_o => left_tree_out_s);

			right_tree : entity work.add_tree(rtl)
			generic map (
				pipelined_g  => pipelined_g,
				num_inputs_g => natural(num_inputs_g/2),
				data_width_g => data_width_g)
			port map (
				clk_i    => clk_i,
				rst_i    => rst_i,
				en_i     => en_i,
				input_i  => input_s(data_width_g * natural(num_inputs_g/2) - 1 downto 0),
				output_o => right_tree_out_unaligned_s);

			right_tree_out_s <= right_tree_out_unaligned_s;

		end generate even_input_number_gen;
		

		pipelined_gen : if pipelined_g = true generate

			delay_right_tree_gen : if num_inputs_g mod 2 /= 0 generate
				
				depth_diff_greater_0_gen : if depth_diff_c > 0 generate
					process(clk_i)
					begin
						if (rising_edge(clk_i)) then
							if (rst_i = '1') then
								delay_reg <= (others => '0');
							else
								if (en_i = '1') then
									delay_reg(data_width_g - 1 downto 0) <= right_tree_out_unaligned_s;
								end if;
				
								for i in 0 to depth_diff_c - 2 loop
									if (en_i = '1') then
										delay_reg(data_width_g * (i + 2) - 1 downto data_width_g * (i + 1)) 
											<= delay_reg(data_width_g * (i + 1) - 1 downto data_width_g * i);
									end if;
								end loop;
							end if;
						end if;
					end process;

					right_tree_out_s <= delay_reg(depth_diff_c * data_width_g - 1 downto (depth_diff_c - 1) * data_width_g);
				
				end generate depth_diff_greater_0_gen;

				depth_diff_equal_0_gen : if depth_diff_c = 0 generate
					right_tree_out_s <= right_tree_out_unaligned_s;
				end generate depth_diff_equal_0_gen;

			end generate delay_right_tree_gen;

			process(clk_i)
			begin
				if (rising_edge(clk_i)) then
					if (rst_i = '1') then
						output_s <= (others => '0');
					elsif (en_i = '1') then
						output_s <= mod_adder_subtrees_out_s;
					end if;
				end if;
			end process;
		end generate pipelined_gen;
		
		not_pipelined_gen : if pipelined_g = false generate
			unaligned_not_pipelined_gen : if num_inputs_g mod 2 /= 0 generate
				right_tree_out_s <= right_tree_out_unaligned_s;
			end generate unaligned_not_pipelined_gen;
			output_s <= mod_adder_subtrees_out_s;
		end generate not_pipelined_gen;

	end generate greater_two_input_gen;
	

end rtl;
